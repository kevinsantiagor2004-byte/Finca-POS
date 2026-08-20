using FluentAssertions;
using ProyectoFinca.Infrastructure.Services;

namespace ProyectoFinca.Tests.Services;

/// <summary>
/// Pruebas unitarias para PasswordService (BCrypt).
/// Verifican que el hashing y la verificación de contraseñas funcionen correctamente.
/// </summary>
public class PasswordServiceTests
{
    private readonly PasswordService _sut = new();

    [Fact]
    public void HashPassword_DebeRetornarHashDistintoAlTextoPlano()
    {
        // Arrange
        const string password = "Admin@2024!";

        // Act
        var hash = _sut.HashPassword(password);

        // Assert
        hash.Should().NotBe(password);
        // Formato BCrypt — siempre empieza con $2a$ o $2b$
        (hash.StartsWith("$2a$") || hash.StartsWith("$2b$"))
            .Should().BeTrue("el hash debe tener formato BCrypt");
    }

    [Fact]
    public void HashPassword_DosHashesDeLaMismaContrasenaDiferencian()
    {
        // Cada BCrypt genera un salt diferente — dos hashes NUNCA son iguales
        const string password = "MismaContraseña!";

        var hash1 = _sut.HashPassword(password);
        var hash2 = _sut.HashPassword(password);

        hash1.Should().NotBe(hash2, "BCrypt usa salt aleatorio en cada hash");
    }

    [Theory]
    [InlineData("Admin@2024!", true)]
    [InlineData("ContraseñaIncorrecta", false)]
    [InlineData("", false)]
    [InlineData("admin@2024!", false)] // Case-sensitive
    public void VerifyPassword_DebeBehaviourCorrecto(string input, bool esperadoValido)
    {
        // Arrange
        const string original = "Admin@2024!";
        var hash = _sut.HashPassword(original);

        // Act
        var resultado = _sut.VerifyPassword(input, hash);

        // Assert
        resultado.Should().Be(esperadoValido);
    }

    [Fact]
    public void VerifyPassword_ConHashTampeado_DebeRetornarFalse()
    {
        const string password = "Segura@123!";
        var hash = _sut.HashPassword(password);

        // Tamper the hash
        var hashTampeado = hash[..^5] + "XXXXX";

        var resultado = _sut.VerifyPassword(password, hashTampeado);

        resultado.Should().BeFalse();
    }
}
