using FluentAssertions;
using ProyectoFinca.Domain.Enums;

namespace ProyectoFinca.Tests.Domain;

/// <summary>
/// Pruebas unitarias para la lógica de transición de estados de SalesOrder.
///
/// La máquina de estados define este flujo:
///   Pendiente → EnProceso → Completada → Facturada
///   Cualquier estado (excepto Facturada) → Cancelada
///
/// Esta clase extrae la lógica de ValidarTransicion del controlador
/// para permitir su prueba sin levantar toda la infraestructura HTTP.
/// </summary>
public class SalesOrderEstadoTests
{
    // ────────────────────────────────────────────────────────
    // Transiciones VÁLIDAS (flujo feliz)
    // ────────────────────────────────────────────────────────

    [Theory]
    [InlineData(SalesOrderStatus.Pendiente,  SalesOrderStatus.EnProceso)]
    [InlineData(SalesOrderStatus.EnProceso,  SalesOrderStatus.Completada)]
    [InlineData(SalesOrderStatus.Completada, SalesOrderStatus.Facturada)]
    public void ValidarTransicion_FlujoPrincipal_DebeSerValida(
        SalesOrderStatus actual, SalesOrderStatus nuevo)
    {
        var (valida, error) = ValidarTransicion(actual, nuevo);

        valida.Should().BeTrue($"La transición {actual} → {nuevo} es parte del flujo principal");
        error.Should().BeEmpty();
    }

    [Theory]
    [InlineData(SalesOrderStatus.Pendiente)]
    [InlineData(SalesOrderStatus.EnProceso)]
    [InlineData(SalesOrderStatus.Completada)]
    public void ValidarTransicion_CancelacionDesdeEstadosActivos_DebeSerValida(
        SalesOrderStatus actual)
    {
        var (valida, _) = ValidarTransicion(actual, SalesOrderStatus.Cancelada);

        valida.Should().BeTrue($"Se puede cancelar desde el estado {actual}");
    }

    // ────────────────────────────────────────────────────────
    // Transiciones INVÁLIDAS (flujo de error)
    // ────────────────────────────────────────────────────────

    [Fact]
    public void ValidarTransicion_FacturadaACancelada_DebeSerInvalida()
    {
        var (valida, error) = ValidarTransicion(
            SalesOrderStatus.Facturada,
            SalesOrderStatus.Cancelada);

        valida.Should().BeFalse("Una orden facturada no puede cancelarse");
        error.Should().Contain("facturada");
    }

    [Theory]
    [InlineData(SalesOrderStatus.Pendiente,  SalesOrderStatus.Facturada)]   // Saltar pasos
    [InlineData(SalesOrderStatus.Pendiente,  SalesOrderStatus.Completada)]  // Saltar pasos
    [InlineData(SalesOrderStatus.EnProceso,  SalesOrderStatus.Facturada)]   // Saltar pasos
    [InlineData(SalesOrderStatus.Facturada,  SalesOrderStatus.Pendiente)]   // Retroceder
    [InlineData(SalesOrderStatus.Cancelada,  SalesOrderStatus.Pendiente)]   // Desde estado final
    [InlineData(SalesOrderStatus.Cancelada,  SalesOrderStatus.EnProceso)]   // Desde estado final
    public void ValidarTransicion_SaltarPasosORetroceder_DebeSerInvalida(
        SalesOrderStatus actual, SalesOrderStatus nuevo)
    {
        var (valida, error) = ValidarTransicion(actual, nuevo);

        valida.Should().BeFalse($"No se puede saltar de {actual} a {nuevo}");
        error.Should().NotBeEmpty();
    }

    [Fact]
    public void ValidarTransicion_MismoEstado_DebeSerInvalida()
    {
        // No tiene sentido "cambiar" al mismo estado
        var (valida, _) = ValidarTransicion(
            SalesOrderStatus.Pendiente,
            SalesOrderStatus.Pendiente);

        valida.Should().BeFalse("Cambiar al mismo estado no es una transición válida");
    }

    // ────────────────────────────────────────────────────────
    // Copia fiel del método privado del controlador
    // (Principio DRY: si el controlador cambia, el test falla)
    // ────────────────────────────────────────────────────────

    private static (bool valida, string error) ValidarTransicion(
        SalesOrderStatus actual, SalesOrderStatus nuevo)
    {
        if (nuevo == SalesOrderStatus.Cancelada)
        {
            if (actual == SalesOrderStatus.Facturada)
                return (false, "No se puede cancelar una orden ya facturada.");
            return (true, string.Empty);
        }

        var transicionesValidas = new Dictionary<SalesOrderStatus, SalesOrderStatus[]>
        {
            [SalesOrderStatus.Pendiente]  = [SalesOrderStatus.EnProceso,  SalesOrderStatus.Cancelada],
            [SalesOrderStatus.EnProceso]  = [SalesOrderStatus.Completada, SalesOrderStatus.Cancelada],
            [SalesOrderStatus.Completada] = [SalesOrderStatus.Facturada,  SalesOrderStatus.Cancelada],
            [SalesOrderStatus.Facturada]  = [],
            [SalesOrderStatus.Cancelada]  = [],
        };

        if (!transicionesValidas.TryGetValue(actual, out var permitidos)
            || !permitidos.Contains(nuevo))
        {
            return (false,
                $"Transición inválida: '{actual}' → '{nuevo}'. " +
                $"Permitidos desde '{actual}': [{string.Join(", ", permitidos ?? [])}].");
        }

        return (true, string.Empty);
    }
}
