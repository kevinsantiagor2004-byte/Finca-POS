using FluentAssertions;
using ProyectoFinca.Domain.Entities;
using ProyectoFinca.Domain.Enums;

namespace ProyectoFinca.Tests.Domain;

/// <summary>
/// Pruebas unitarias para la lógica de cálculo de precios de SalesOrder.
///
/// Valida la fórmula:
///   Subtotal = PrecioBase + Σ(ServiciosObligatorios) + Σ(ServiciosOpcionalesSeleccionados)
///   Total    = (Subtotal - Descuento) × (1 + PorcentajeImpuesto)
/// </summary>
public class SalesOrderPrecioTests
{
    // ── Helpers para construir entidades de prueba ───────────────────────────

    private static Plan CrearPlan(decimal precioBase) => new()
    {
        Id        = Guid.NewGuid(),
        Nombre    = "Plan de Prueba",
        PrecioBase = precioBase,
        IsActive  = true
    };

    private static Service CrearServicio(string nombre, decimal precio) => new()
    {
        Id              = Guid.NewGuid(),
        Nombre          = nombre,
        PrecioAdicional = precio,
        IsActive        = true
    };

    private static PlanService AgregarServicioAPlan(Plan plan, Service service,
        bool esObligatorio, decimal? precioEspecial = null)
    {
        var ps = new PlanService
        {
            PlanId        = plan.Id,
            ServiceId     = service.Id,
            Plan          = plan,
            Service       = service,
            EsObligatorio = esObligatorio,
            PrecioEspecial = precioEspecial
        };
        plan.PlanServices.Add(ps);
        return ps;
    }

    // ── Tests ────────────────────────────────────────────────────────────────

    [Fact]
    public void Precio_SoloPrecioBase_SinServicios()
    {
        var plan = CrearPlan(100m);

        var (subtotal, _) = CalcularPrecio(plan, [], 0m, 0m);

        subtotal.Should().Be(100m);
    }

    [Fact]
    public void Precio_ServicioObligatorioSeSumaAutomaticamente()
    {
        var plan      = CrearPlan(100m);
        var desayuno  = CrearServicio("Desayuno", 30m);
        AgregarServicioAPlan(plan, desayuno, esObligatorio: true);

        var (subtotal, _) = CalcularPrecio(plan, [], 0m, 0m);

        subtotal.Should().Be(130m, "PrecioBase(100) + Desayuno obligatorio(30)");
    }

    [Fact]
    public void Precio_ServicioObligatorioConPrecioEspecialUsaEseValor()
    {
        var plan     = CrearPlan(100m);
        var masaje   = CrearServicio("Masaje", 80m);
        AgregarServicioAPlan(plan, masaje, esObligatorio: true, precioEspecial: 50m); // Descuento de plan

        var (subtotal, _) = CalcularPrecio(plan, [], 0m, 0m);

        subtotal.Should().Be(150m, "Usa PrecioEspecial(50) no PrecioAdicional(80)");
    }

    [Fact]
    public void Precio_ServicioOpcionalSeleccionadoSeSuma()
    {
        var plan    = CrearPlan(100m);
        var masaje  = CrearServicio("Masaje", 80m);
        var ps      = AgregarServicioAPlan(plan, masaje, esObligatorio: false);

        var opcionalesSeleccionados = new[] { masaje.Id };
        var (subtotal, _) = CalcularPrecio(plan, opcionalesSeleccionados, 0m, 0m);

        subtotal.Should().Be(180m, "PrecioBase(100) + Masaje opcional seleccionado(80)");
    }

    [Fact]
    public void Precio_ServicioOpcionalNoSeleccionadoNoSeSuma()
    {
        var plan   = CrearPlan(100m);
        var masaje = CrearServicio("Masaje", 80m);
        AgregarServicioAPlan(plan, masaje, esObligatorio: false);

        // No se selecciona el masaje
        var (subtotal, _) = CalcularPrecio(plan, [], 0m, 0m);

        subtotal.Should().Be(100m, "Solo PrecioBase, el opcional no fue seleccionado");
    }

    [Fact]
    public void Precio_ImpuestoSeAplicaSobreSubtotalMenosDescuento()
    {
        var plan = CrearPlan(1000m);
        decimal descuento   = 100m;  // -100
        decimal impuesto    = 0.13m; // 13% IVA
        // (1000 - 100) * 1.13 = 900 * 1.13 = 1017

        var (_, total) = CalcularPrecio(plan, [], descuento, impuesto);

        total.Should().Be(1017m);
    }

    [Fact]
    public void Precio_EscenarioCompletoFinca()
    {
        // Escenario: Plan Eco-Turismo con desayuno obligatorio,
        // masaje opcional seleccionado, descuento especial y 13% IVA

        var plan     = CrearPlan(500m);
        var desayuno = CrearServicio("Desayuno", 30m);
        var masaje   = CrearServicio("Masaje", 80m);
        var tour     = CrearServicio("Tour", 60m);

        AgregarServicioAPlan(plan, desayuno, esObligatorio: true);              // +30 (obligatorio)
        AgregarServicioAPlan(plan, masaje,   esObligatorio: false);             // +80 (opcional, seleccionado)
        AgregarServicioAPlan(plan, tour,     esObligatorio: false);             // no seleccionado

        var opcionalesSeleccionados = new[] { masaje.Id }; // Solo masaje
        decimal descuento   = 50m;
        decimal impuesto    = 0.13m;

        // Subtotal = 500 + 30 + 80 = 610
        // Total    = (610 - 50) * 1.13 = 560 * 1.13 = 632.80

        var (subtotal, total) = CalcularPrecio(plan, opcionalesSeleccionados, descuento, impuesto);

        subtotal.Should().Be(610m);
        total.Should().Be(632.80m);
    }

    // ── Motor de cálculo de precios (extraído del controlador para testabilidad) ──

    private static (decimal subtotal, decimal total) CalcularPrecio(
        Plan plan,
        IEnumerable<Guid> opcionalesSeleccionados,
        decimal descuento,
        decimal impuesto)
    {
        decimal subtotal = plan.PrecioBase;

        // Servicios obligatorios
        foreach (var ps in plan.PlanServices.Where(ps => ps.EsObligatorio))
        {
            subtotal += ps.PrecioEspecial ?? ps.Service.PrecioAdicional;
        }

        // Servicios opcionales seleccionados
        var disponibles = plan.PlanServices
            .Where(ps => !ps.EsObligatorio)
            .ToDictionary(ps => ps.ServiceId);

        foreach (var serviceId in opcionalesSeleccionados)
        {
            if (disponibles.TryGetValue(serviceId, out var ps))
                subtotal += ps.PrecioEspecial ?? ps.Service.PrecioAdicional;
        }

        var total = Math.Round((subtotal - descuento) * (1 + impuesto), 2);
        return (subtotal, total);
    }
}
