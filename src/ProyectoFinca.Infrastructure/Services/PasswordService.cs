using ProyectoFinca.Application.Interfaces;
using BC = BCrypt.Net.BCrypt;

namespace ProyectoFinca.Infrastructure.Services;

/// <summary>
/// Implementación de <see cref="IPasswordService"/> usando BCrypt con work factor 12.
///
/// BCrypt genera automáticamente un salt único por contraseña,
/// por lo que el mismo texto plano produce hashes distintos en cada llamada.
/// La verificación siempre usa el salt embebido en el hash almacenado.
/// </summary>
public class PasswordService : IPasswordService
{
    /// <summary>
    /// Work factor de BCrypt. Cada incremento de 1 duplica el tiempo de cómputo.
    /// Factor 12 ≈ 250ms por hash en hardware moderno — balance seguridad/UX.
    /// </summary>
    private const int WorkFactor = 12;

    /// <inheritdoc/>
    public string HashPassword(string plainPassword)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(plainPassword, nameof(plainPassword));
        return BC.HashPassword(plainPassword, WorkFactor);
    }

    /// <inheritdoc/>
    public bool VerifyPassword(string plainPassword, string hashedPassword)
    {
        if (string.IsNullOrWhiteSpace(plainPassword) || string.IsNullOrWhiteSpace(hashedPassword))
            return false;

        // BCrypt.Verify es timing-safe — no vulnerable a ataques de tiempo
        return BC.Verify(plainPassword, hashedPassword);
    }
}
