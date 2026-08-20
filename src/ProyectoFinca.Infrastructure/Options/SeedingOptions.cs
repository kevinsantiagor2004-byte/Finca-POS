namespace ProyectoFinca.Infrastructure.Options;

/// <summary>
/// Opciones para la siembra de datos iniciales (Data Seeding).
/// Se leen desde appsettings.json → sección "Seeding".
///
/// ⚠️ IMPORTANTE: Cambia la contraseña del admin por defecto
/// en cuanto el sistema esté en producción.
/// </summary>
public class SeedingOptions
{
    public const string SectionName = "Seeding";

    /// <summary>
    /// Indica si el seeder está habilitado.
    /// En producción puedes desactivarlo con "Seeding:Enabled": false.
    /// </summary>
    public bool Enabled { get; set; } = true;

    // -----------------------------------------------
    // Admin inicial
    // -----------------------------------------------

    /// <summary>Nombre completo del usuario administrador inicial.</summary>
    public string AdminNombreCompleto { get; set; } = "Administrador del Sistema";

    /// <summary>Email del administrador inicial.</summary>
    public string AdminEmail { get; set; } = "admin@finca.com";

    /// <summary>
    /// Contraseña en texto plano del admin inicial.
    /// El sistema la convertirá en hash BCrypt antes de guardarla.
    /// Cumple los requisitos: ≥8 chars, 1 mayúscula, 1 número.
    /// </summary>
    public string AdminPassword { get; set; } = "Admin@2024!";

    /// <summary>Teléfono de contacto del admin (opcional).</summary>
    public string? AdminTelefono { get; set; } = null;
}
