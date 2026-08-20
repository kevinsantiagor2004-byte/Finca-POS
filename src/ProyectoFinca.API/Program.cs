using System.Text;
using System.Threading.RateLimiting;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Diagnostics.HealthChecks;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Diagnostics.HealthChecks;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;
using ProyectoFinca.Infrastructure;
using ProyectoFinca.Infrastructure.Options;
using ProyectoFinca.Infrastructure.Persistence;
using ProyectoFinca.Infrastructure.Seeding;

var builder = WebApplication.CreateBuilder(args);

// =========================================================
// 1. Infrastructure: EF Core + BCrypt + JWT + Seeding
// =========================================================
builder.Services.AddInfrastructure(builder.Configuration);

// =========================================================
// 2. CORS — Orígenes permitidos por ambiente
// =========================================================
var allowedOrigins = builder.Configuration
    .GetSection("Cors:AllowedOrigins")
    .Get<string[]>() ?? ["http://localhost:3000", "http://localhost:5173"];

builder.Services.AddCors(options =>
{
    options.AddPolicy("FincaPolicy", policy =>
    {
        policy.WithOrigins(allowedOrigins)
              .AllowAnyMethod()
              .AllowAnyHeader()
              .WithExposedHeaders("X-Pagination"); // Para metadatos de paginación
    });

    // Política permisiva solo para Development
    if (builder.Environment.IsDevelopment())
    {
        options.AddPolicy("FincaDevPolicy", policy =>
            policy.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader());
    }
});

// =========================================================
// 3. Rate Limiting — Protección contra fuerza bruta
// =========================================================
builder.Services.AddRateLimiter(options =>
{
    // Política para Login: máximo 5 intentos por minuto por IP
    options.AddFixedWindowLimiter("auth-login", opt =>
    {
        opt.PermitLimit         = 5;
        opt.Window              = TimeSpan.FromMinutes(1);
        opt.QueueProcessingOrder = QueueProcessingOrder.OldestFirst;
        opt.QueueLimit          = 0;
    });

    // Política global: 100 req/minuto por IP para todos los endpoints
    options.AddFixedWindowLimiter("api-global", opt =>
    {
        opt.PermitLimit         = 100;
        opt.Window              = TimeSpan.FromMinutes(1);
        opt.QueueProcessingOrder = QueueProcessingOrder.OldestFirst;
        opt.QueueLimit          = 10;
    });

    // Respuesta personalizada al superar el límite
    options.OnRejected = async (context, token) =>
    {
        context.HttpContext.Response.StatusCode  = 429;
        context.HttpContext.Response.ContentType = "application/json";

        var retryAfter = context.Lease.TryGetMetadata(
            MetadataName.RetryAfter, out var retry) ? (int)retry.TotalSeconds : 60;

        await context.HttpContext.Response.WriteAsync(
            $"{{\"status\":429,\"error\":\"Demasiadas solicitudes. Intenta de nuevo en {retryAfter} segundos.\"}}",
            token);
    };
});

// =========================================================
// 4. Autenticación JWT
// =========================================================
var jwtSection = builder.Configuration.GetSection(JwtOptions.SectionName);
var jwtKey     = jwtSection["Key"]
    ?? throw new InvalidOperationException("Jwt:Key no configurado.");

builder.Services
    .AddAuthentication(options =>
    {
        options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
        options.DefaultChallengeScheme    = JwtBearerDefaults.AuthenticationScheme;
    })
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer           = true,
            ValidIssuer              = jwtSection["Issuer"],
            ValidateAudience         = true,
            ValidAudience            = jwtSection["Audience"],
            ValidateIssuerSigningKey = true,
            IssuerSigningKey         = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey)),
            ValidateLifetime         = true,
            ClockSkew                = TimeSpan.Zero,
            RoleClaimType            = System.Security.Claims.ClaimTypes.Role,
        };

        options.Events = new JwtBearerEvents
        {
            OnChallenge = ctx =>
            {
                ctx.HandleResponse();
                ctx.Response.StatusCode  = 401;
                ctx.Response.ContentType = "application/json";
                return ctx.Response.WriteAsync(
                    """{"status":401,"error":"No autorizado. Incluye el token JWT en el header Authorization: Bearer {token}"}""");
            },
            OnForbidden = ctx =>
            {
                ctx.Response.StatusCode  = 403;
                ctx.Response.ContentType = "application/json";
                return ctx.Response.WriteAsync(
                    """{"status":403,"error":"Acceso denegado. Tu rol no tiene permiso para esta operación."}""");
            }
        };
    });

builder.Services.AddAuthorizationBuilder();

// =========================================================
// 5. Health Checks — /health/live y /health/ready
// =========================================================
var connectionString = builder.Configuration.GetConnectionString("DefaultConnection")!;

builder.Services
    .AddHealthChecks()
    .AddNpgSql(
        connectionString,
        name:    "postgresql",
        tags:    ["ready", "db"],
        timeout: TimeSpan.FromSeconds(5))
    .AddCheck("api", () => HealthCheckResult.Healthy("API operativa"), tags: ["live"]);

// =========================================================
// 6. Controllers + Swagger con soporte JWT
// =========================================================
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new OpenApiInfo
    {
        Title       = "Proyecto Finca — POS API",
        Version     = "v1",
        Description = "API del sistema POS para la Finca/Hotel.\n\n" +
                      "**Autenticación**: Usa `POST /api/auth/login` para obtener el token JWT.\n" +
                      "Luego haz clic en **Authorize** e ingresa: `Bearer {tu_token}`"
    });

    options.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Name         = "Authorization",
        Type         = SecuritySchemeType.ApiKey,
        Scheme       = "Bearer",
        BearerFormat = "JWT",
        In           = ParameterLocation.Header,
        Description  = "Ingresa el token JWT con el prefijo **Bearer**.\n\nEjemplo: `Bearer eyJhbGci...`"
    });

    options.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecurityScheme
            {
                Reference = new OpenApiReference { Type = ReferenceType.SecurityScheme, Id = "Bearer" }
            },
            Array.Empty<string>()
        }
    });
});

// =========================================================
// Build
// =========================================================
var app = builder.Build();

// =========================================================
// Pipeline HTTP
// =========================================================

// Swagger solo en Development
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI(options =>
    {
        options.SwaggerEndpoint("/swagger/v1/swagger.json", "ProyectoFinca POS v1");
        options.RoutePrefix = string.Empty;
        options.DocExpansion(Swashbuckle.AspNetCore.SwaggerUI.DocExpansion.None);
        options.DisplayRequestDuration();
    });
}

// CORS — usar política permisiva en DEV, restrictiva en QA/PRD
var corsPolicy = app.Environment.IsDevelopment() ? "FincaDevPolicy" : "FincaPolicy";
app.UseCors(corsPolicy);

// Rate Limiting
app.UseRateLimiter();

// Cabeceras de seguridad HTTP
app.Use(async (context, next) =>
{
    context.Response.Headers["X-Content-Type-Options"]    = "nosniff";
    context.Response.Headers["X-Frame-Options"]           = "DENY";
    context.Response.Headers["X-XSS-Protection"]          = "1; mode=block";
    context.Response.Headers["Referrer-Policy"]           = "no-referrer";
    context.Response.Headers["Permissions-Policy"]        = "camera=(), microphone=(), geolocation=()";
    if (!app.Environment.IsDevelopment())
        context.Response.Headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains";
    await next();
});

app.UseHttpsRedirection();
app.UseAuthentication();
app.UseAuthorization();

// Health Checks — sin autenticación para que los balanceadores puedan acceder
app.MapHealthChecks("/health/live", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("live"),
    ResponseWriter = async (ctx, report) =>
    {
        ctx.Response.ContentType = "application/json";
        var result = new
        {
            status    = report.Status.ToString(),
            timestamp = DateTime.UtcNow
        };
        await ctx.Response.WriteAsJsonAsync(result);
    }
}).AllowAnonymous();

app.MapHealthChecks("/health/ready", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("ready"),
    ResponseWriter = async (ctx, report) =>
    {
        ctx.Response.ContentType = "application/json";
        var result = new
        {
            status  = report.Status.ToString(),
            checks  = report.Entries.Select(e => new
            {
                name     = e.Key,
                status   = e.Value.Status.ToString(),
                duration = e.Value.Duration.TotalMilliseconds + "ms"
            })
        };
        await ctx.Response.WriteAsJsonAsync(result);
    }
}).AllowAnonymous();

app.MapControllers();

// =========================================================
// Seeding — Migraciones + Usuario Admin inicial
// =========================================================
await DbInitializer.SeedAsync(app.Services);

await app.RunAsync();
