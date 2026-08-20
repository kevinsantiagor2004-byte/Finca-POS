using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using ProyectoFinca.Application.Interfaces;
using ProyectoFinca.Domain.Entities;
using ProyectoFinca.Domain.Enums;
using ProyectoFinca.Infrastructure.Options;
using ProyectoFinca.Infrastructure.Persistence;

namespace ProyectoFinca.Infrastructure.Seeding;

/// <summary>
/// Inicializador de datos base del sistema POS.
///
/// Se ejecuta al arrancar la aplicación (en Program.cs) y garantiza que:
///   1. La base de datos tenga aplicadas todas las migraciones pendientes.
///   2. Exista al menos un usuario con rol Admin para poder iniciar sesión.
///
/// El seeder es IDEMPOTENTE: si los datos ya existen, no hace nada.
/// Puede desactivarse con "Seeding:Enabled": false en appsettings.json.
/// </summary>
public static class DbInitializer
{
    /// <summary>
    /// Punto de entrada del seeder. Llamar desde Program.cs después del Build().
    /// Crea su propio scope para resolver servicios scoped (DbContext, IPasswordService).
    /// </summary>
    /// <param name="serviceProvider">El IServiceProvider raíz de la aplicación.</param>
    public static async Task SeedAsync(IServiceProvider serviceProvider)
    {
        // Crear scope propio (DbContext e IPasswordService son Scoped)
        await using var scope = serviceProvider.CreateAsyncScope();
        var sp = scope.ServiceProvider;

        var logger  = sp.GetRequiredService<ILogger<ApplicationDbContext>>();
        var opts    = sp.GetRequiredService<IOptions<SeedingOptions>>().Value;

        if (!opts.Enabled)
        {
            logger.LogInformation("[DbInitializer] Seeding desactivado en configuración. Se omite.");
            return;
        }

        var context         = sp.GetRequiredService<ApplicationDbContext>();
        var passwordService = sp.GetRequiredService<IPasswordService>();

        try
        {
            // -----------------------------------------------
            // 1. Aplicar migraciones pendientes (si las hay)
            // -----------------------------------------------
            var pendientes = await context.Database.GetPendingMigrationsAsync();
            if (pendientes.Any())
            {
                logger.LogInformation("[DbInitializer] Aplicando {Count} migración(es) pendiente(s)...",
                    pendientes.Count());
                await context.Database.MigrateAsync();
                logger.LogInformation("[DbInitializer] Migraciones aplicadas correctamente.");
            }

            // -----------------------------------------------
            // 2. Semilla: Usuario Administrador inicial
            // -----------------------------------------------
            await SeedAdminUsuarioAsync(context, passwordService, opts, logger);
        }
        catch (Exception ex)
        {
            logger.LogError(ex,
                "[DbInitializer] Error crítico durante el seeding de la base de datos. " +
                "Verifica la conexión y el estado de las migraciones.");
            throw; // Re-lanzar para que la app no arranque en estado inconsistente
        }
    }

    // =========================================================
    // Seeder privado: Usuario Admin
    // =========================================================

    private static async Task SeedAdminUsuarioAsync(
        ApplicationDbContext context,
        IPasswordService passwordService,
        SeedingOptions opts,
        ILogger logger)
    {
        // IgnoreQueryFilters() para incluir soft-deleted y evitar duplicados
        var adminExiste = await context.Usuarios
            .IgnoreQueryFilters()
            .AnyAsync(u => u.Email.ToLower() == opts.AdminEmail.ToLower());

        if (adminExiste)
        {
            logger.LogDebug(
                "[DbInitializer] El usuario Admin '{Email}' ya existe. Seeding omitido.",
                opts.AdminEmail);
            return;
        }

        // Hashear la contraseña usando IPasswordService (BCrypt work factor 12)
        // Esto garantiza que NUNCA se almacena texto plano en la BD.
        var passwordHash = passwordService.HashPassword(opts.AdminPassword);

        var admin = new Usuario
        {
            // BaseEntity se encarga de Id (Guid.NewGuid), CreatedAt y UpdatedAt
            NombreCompleto = opts.AdminNombreCompleto,
            Email          = opts.AdminEmail.ToLower().Trim(),
            PasswordHash   = passwordHash,
            Telefono       = opts.AdminTelefono,
            Rol            = UserRole.Admin,
            IsActive       = true,
            IsDeleted      = false
        };

        context.Usuarios.Add(admin);
        await context.SaveChangesAsync();

        // ⚠️ Loguear a nivel Warning para que sea visible incluso en producción.
        //    NO logueamos la contraseña, solo el email.
        logger.LogWarning(
            "[DbInitializer] ✅ Usuario Admin inicial creado." +
            " Email: {Email} | Por favor cambia la contraseña por defecto en producción.",
            admin.Email);
    }
}
