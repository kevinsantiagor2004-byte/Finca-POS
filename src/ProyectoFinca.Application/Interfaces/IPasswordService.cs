namespace ProyectoFinca.Application.Interfaces;

/// <summary>
/// Contrato para el servicio de hashing y verificación de contraseñas.
/// La implementación usa BCrypt con work factor 12 para máxima seguridad.
///
/// Principios de seguridad aplicados:
///   - Nunca se almacena la contraseña en texto plano.
///   - Cada hash es único gracias al salt automático de BCrypt.
///   - El work factor 12 es resistente a ataques de fuerza bruta actuales.
/// </summary>
public interface IPasswordService
{
    /// <summary>
    /// Genera un hash seguro de una contraseña en texto plano.
    /// </summary>
    /// <param name="plainPassword">Contraseña en texto plano proporcionada por el usuario.</param>
    /// <returns>Hash BCrypt con salt embebido, listo para almacenarse en la base de datos.</returns>
    string HashPassword(string plainPassword);

    /// <summary>
    /// Verifica si una contraseña en texto plano coincide con un hash almacenado.
    /// </summary>
    /// <param name="plainPassword">Contraseña en texto plano a verificar.</param>
    /// <param name="hashedPassword">Hash almacenado en la base de datos.</param>
    /// <returns>True si la contraseña es correcta; false en caso contrario.</returns>
    bool VerifyPassword(string plainPassword, string hashedPassword);
}
