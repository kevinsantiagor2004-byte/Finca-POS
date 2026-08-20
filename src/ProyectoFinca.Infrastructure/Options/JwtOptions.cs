namespace ProyectoFinca.Infrastructure.Options;

/// <summary>
/// Opciones de configuración JWT leídas desde appsettings.json → sección "Jwt".
/// Se registran con IOptions&lt;JwtOptions&gt; en el contenedor de DI.
/// </summary>
public class JwtOptions
{
    /// <summary>Nombre de la sección en appsettings.json.</summary>
    public const string SectionName = "Jwt";

    /// <summary>
    /// Clave secreta usada para firmar los tokens (HMAC-SHA256).
    /// Debe tener al menos 32 caracteres. NUNCA exponerla en código fuente.
    /// Usar variables de entorno o User Secrets en producción.
    /// </summary>
    public string Key { get; set; } = string.Empty;

    /// <summary>Emisor del token (valor del claim "iss").</summary>
    public string Issuer { get; set; } = "ProyectoFinca.API";

    /// <summary>Audiencia del token (valor del claim "aud").</summary>
    public string Audience { get; set; } = "ProyectoFinca.Clients";

    /// <summary>Horas de validez del token desde su emisión. Por defecto: 8 horas.</summary>
    public int ExpiresInHours { get; set; } = 8;
}
