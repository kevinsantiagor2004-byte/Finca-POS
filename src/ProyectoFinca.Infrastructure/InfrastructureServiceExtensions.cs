using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using ProyectoFinca.Application.Interfaces;
using ProyectoFinca.Infrastructure.Options;
using ProyectoFinca.Infrastructure.Persistence;
using ProyectoFinca.Infrastructure.Services;

namespace ProyectoFinca.Infrastructure;

/// <summary>
/// Extensión de IServiceCollection para registrar todos los servicios
/// de Infrastructure (EF Core, BCrypt, JWT) en el contenedor de DI.
///
/// El middleware JWT (AddAuthentication/AddJwtBearer) se registra
/// en Program.cs (API layer) porque requiere paquetes de AspNetCore.
/// </summary>
public static class InfrastructureServiceExtensions
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        // -----------------------------------------------
        // Opciones fuertemente tipadas
        // -----------------------------------------------
        services.Configure<JwtOptions>(
            configuration.GetSection(JwtOptions.SectionName));

        services.Configure<PosOptions>(
            configuration.GetSection(PosOptions.SectionName));

        services.Configure<SeedingOptions>(
            configuration.GetSection(SeedingOptions.SectionName));

        // -----------------------------------------------
        // Entity Framework Core — PostgreSQL
        // -----------------------------------------------
        var connectionString = configuration.GetConnectionString("DefaultConnection")
            ?? throw new InvalidOperationException(
                "Cadena de conexión 'DefaultConnection' no encontrada en appsettings.json.");

        services.AddDbContext<ApplicationDbContext>(options =>
        {
            options.UseNpgsql(connectionString, npgsql =>
            {
                npgsql.MigrationsAssembly(typeof(ApplicationDbContext).Assembly.FullName);
                npgsql.EnableRetryOnFailure(
                    maxRetryCount: 3,
                    maxRetryDelay: TimeSpan.FromSeconds(10),
                    errorCodesToAdd: null);
            });
        });

        // Registrar el DbContext como la interfaz (Clean Architecture — DIP)
        services.AddScoped<IApplicationDbContext>(
            sp => sp.GetRequiredService<ApplicationDbContext>());

        // -----------------------------------------------
        // Servicios de negocio (scoped)
        // -----------------------------------------------
        services.AddScoped<IJwtService,      JwtService>();
        services.AddScoped<IPasswordService, PasswordService>();

        return services;
    }
}
