using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;
using ProyectoFinca.Application.Interfaces;
using ProyectoFinca.Domain.Entities;
using ProyectoFinca.Infrastructure.Options;

namespace ProyectoFinca.Infrastructure.Services;

/// <summary>
/// Implementación de <see cref="IJwtService"/> usando HMAC-SHA256.
///
/// Claims incluidos en cada token:
///   sub   → Usuario.Id (Guid)
///   email → Usuario.Email
///   role  → Usuario.Rol.ToString() (Admin | Cajero | Mesero | Cliente)
///   name  → Usuario.NombreCompleto
///   jti   → UUID único del token (permite revocación futura)
///   iat   → Issued At (Unix timestamp UTC)
///   exp   → Expiry según JwtOptions.ExpiresInHours
/// </summary>
public class JwtService : IJwtService
{
    private readonly JwtOptions _opts;
    private readonly SymmetricSecurityKey _signingKey;

    public JwtService(IOptions<JwtOptions> options)
    {
        _opts = options.Value;

        if (string.IsNullOrWhiteSpace(_opts.Key) || _opts.Key.Length < 32)
            throw new InvalidOperationException(
                "La clave JWT debe tener al menos 32 caracteres. " +
                "Configúrela en appsettings.json → Jwt:Key.");

        _signingKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(_opts.Key));
    }

    /// <inheritdoc/>
    public string GenerarToken(Usuario usuario)
    {
        var credentials = new SigningCredentials(_signingKey, SecurityAlgorithms.HmacSha256);

        var claims = new[]
        {
            new Claim(JwtRegisteredClaimNames.Sub,   usuario.Id.ToString()),
            new Claim(JwtRegisteredClaimNames.Email, usuario.Email),
            new Claim(ClaimTypes.Role,               usuario.Rol.ToString()),
            new Claim(JwtRegisteredClaimNames.Name,  usuario.NombreCompleto),
            new Claim(JwtRegisteredClaimNames.Jti,   Guid.NewGuid().ToString()),
            new Claim(JwtRegisteredClaimNames.Iat,
                DateTimeOffset.UtcNow.ToUnixTimeSeconds().ToString(),
                ClaimValueTypes.Integer64),
        };

        var expiry = DateTime.UtcNow.AddHours(_opts.ExpiresInHours);

        var token = new JwtSecurityToken(
            issuer:            _opts.Issuer,
            audience:          _opts.Audience,
            claims:            claims,
            notBefore:         DateTime.UtcNow,
            expires:           expiry,
            signingCredentials: credentials);

        return new JwtSecurityTokenHandler().WriteToken(token);
    }

    /// <inheritdoc/>
    public ClaimsPrincipal? ValidarToken(string token)
    {
        try
        {
            var handler = new JwtSecurityTokenHandler();
            var parameters = new TokenValidationParameters
            {
                ValidateIssuer           = true,
                ValidIssuer              = _opts.Issuer,
                ValidateAudience         = true,
                ValidAudience            = _opts.Audience,
                ValidateIssuerSigningKey = true,
                IssuerSigningKey         = _signingKey,
                ValidateLifetime         = true,
                ClockSkew                = TimeSpan.Zero // Sin margen de tolerancia
            };

            return handler.ValidateToken(token, parameters, out _);
        }
        catch
        {
            return null;
        }
    }

    /// <inheritdoc/>
    public Guid ObtenerUserId(ClaimsPrincipal user)
    {
        var value = user.FindFirst(JwtRegisteredClaimNames.Sub)?.Value
                 ?? user.FindFirst(ClaimTypes.NameIdentifier)?.Value;

        return Guid.TryParse(value, out var id) ? id : Guid.Empty;
    }
}
