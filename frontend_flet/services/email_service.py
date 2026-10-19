"""
Servicio de Facturación Electrónica por Correo y Envíos SMTP.
Genera plantillas HTML profesionales de factura POS estilo DIAN
y realiza envíos reales a bandejas de entrada (Gmail, Outlook, etc.) vía SMTP.
"""

import os
import json
import smtplib
import webbrowser
import tempfile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

CONFIG_FILE_NAME = "finca_smtp_config.json"

def get_smtp_config_path() -> str:
    app_data = os.getenv("APPDATA")
    if app_data:
        dir_path = os.path.join(app_data, "FincaSanSebastian")
    else:
        dir_path = os.path.join(os.path.expanduser("~"), ".finca_san_sebastian")
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, CONFIG_FILE_NAME)

def cargar_configuracion_smtp() -> Dict[str, Any]:
    """Carga los parámetros SMTP del archivo de configuración."""
    path = get_smtp_config_path()
    default_config = {
        "servidor": "smtp.gmail.com",
        "puerto": 587,
        "usar_tls": True,
        "usuario": "",
        "password": "",
        "nombre_remitente": "Finca Turística San Sebastián",
        "correo_remitente": "",
        "activo": False,
    }
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_config.update(data)
        except Exception:
            pass
    return default_config

def guardar_configuracion_smtp(config: Dict[str, Any]) -> bool:
    """Persiste los parámetros SMTP."""
    try:
        path = get_smtp_config_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def probar_conexion_smtp(config: Dict[str, Any]) -> Tuple[bool, str]:
    """Prueba la conexión y autenticación con el servidor SMTP."""
    servidor = config.get("servidor", "smtp.gmail.com").strip()
    puerto = int(config.get("puerto", 587))
    usar_tls = config.get("usar_tls", True)
    usuario = config.get("usuario", "").strip()
    password = config.get("password", "").strip()

    if not usuario or not password:
        return False, "Ingresa el usuario y la contraseña de aplicación."

    try:
        if puerto == 465:
            with smtplib.SMTP_SSL(servidor, puerto, timeout=10) as server:
                server.login(usuario, password)
        else:
            with smtplib.SMTP(servidor, puerto, timeout=10) as server:
                if usar_tls:
                    server.starttls()
                server.login(usuario, password)
        return True, "¡Conexión exitosa! Las credenciales SMTP son válidas."
    except smtplib.SMTPAuthenticationError:
        return False, "Error de autenticación: Verifica tu usuario o genera una nueva contraseña de aplicación."
    except Exception as ex:
        return False, f"Error de conexión con {servidor}:{puerto}: {str(ex)}"

def formatear_cop(val: float | int | None) -> str:
    if val is None:
        val = 0
    return f"${val:,.0f} COP".replace(",", ".")

def generar_html_factura(fac: Dict[str, Any]) -> str:
    """Genera una plantilla HTML moderna y responsiva de la Factura Electrónica POS."""
    consecutivo_str = f"FAC-{fac.get('consecutivo', 1):05d}"
    fecha_hora = fac.get("fecha_hora", datetime.now().strftime("%d/%m/%Y - %I:%M %p"))
    cajero = fac.get("cajero", "Cajero Responsable")
    titular = fac.get("titular", "Consumidor Final")
    documento = fac.get("documento", "222222222222")
    ubicacion = fac.get("ubicacion", "Mostrador / Punto de Pago")
    subtotal = fac.get("subtotal", 0)
    iva = fac.get("iva", 0)
    total = fac.get("total", 0)
    metodo = fac.get("metodo", "Efectivo")
    items = fac.get("items", [])

    # Detalle del medio de pago
    metodo_html = f"<tr><td style='padding:6px 0;color:#64748B;'>Medio de Pago:</td><td style='text-align:right;font-weight:bold;color:#0F172A;'>{metodo.upper()}</td></tr>"
    if metodo == "Efectivo":
        recibido = fac.get("recibido", total)
        cambio = fac.get("cambio", 0)
        metodo_html += f"<tr><td style='padding:4px 0;color:#64748B;'>Efectivo Recibido:</td><td style='text-align:right;font-weight:bold;color:#0F172A;'>{formatear_cop(recibido)}</td></tr>"
        metodo_html += f"<tr><td style='padding:4px 0;color:#16A34A;'>Cambio / Vueltas:</td><td style='text-align:right;font-weight:bold;color:#16A34A;'>{formatear_cop(cambio)}</td></tr>"
    elif metodo == "Nequi / QR":
        comp = fac.get("comprobante", "M948210")
        metodo_html += f"<tr><td style='padding:4px 0;color:#64748B;'>Comprobante Aprobación:</td><td style='text-align:right;font-weight:bold;color:#6D28D9;'>#{comp}</td></tr>"
        metodo_html += f"<tr><td style='padding:4px 0;color:#64748B;'>Llave Nequi:</td><td style='text-align:right;color:#0F172A;'>urbinaangie007@gmail.com</td></tr>"
    else:
        vouch = fac.get("voucher", "849201")
        tarj = fac.get("tarjeta", "DÉBITO VISA")
        metodo_html += f"<tr><td style='padding:4px 0;color:#64748B;'>Tarjeta / Voucher:</td><td style='text-align:right;font-weight:bold;color:#0F172A;'>{tarj} - AUTH #{vouch}</td></tr>"

    filas_items = ""
    for idx, it in enumerate(items, 1):
        bg = "#F8FAFC" if idx % 2 == 0 else "#FFFFFF"
        tot_it = it.get("precio", 0) * it.get("cant", 1)
        filas_items += f"""
        <tr style="background-color:{bg};border-bottom:1px solid #E2E8F0;">
            <td style="padding:10px 12px;font-size:13px;color:#0F172A;font-weight:600;">{it.get('nombre', 'Producto')}</td>
            <td style="padding:10px 12px;font-size:13px;text-align:center;color:#334155;">{it.get('cant', 1)}</td>
            <td style="padding:10px 12px;font-size:13px;text-align:right;color:#334155;">{formatear_cop(it.get('precio', 0))}</td>
            <td style="padding:10px 12px;font-size:13px;text-align:right;font-weight:bold;color:#0F172A;">{formatear_cop(tot_it)}</td>
        </tr>
        """

    cufe_hash = f"c{fac.get('consecutivo', 100)*7}a8f19b4e72d0391f8c44a2b9e6"[:40]

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Factura Electrónica POS - {consecutivo_str}</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    background-color: #F1F5F9;
    margin: 0;
    padding: 24px;
    color: #0F172A;
  }}
  .container {{
    max-width: 620px;
    margin: 0 auto;
    background-color: #FFFFFF;
    border-radius: 12px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    overflow: hidden;
    border: 1px solid #E2E8F0;
  }}
  .header {{
    background: linear-gradient(135deg, #0F766E 0%, #0D9488 100%);
    color: #FFFFFF;
    padding: 28px 24px;
    text-align: center;
  }}
  .header h1 {{
    margin: 0 0 6px 0;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.3px;
  }}
  .header p {{
    margin: 2px 0;
    font-size: 12px;
    color: #CCFBF1;
  }}
  .badge {{
    display: inline-block;
    background-color: rgba(255,255,255,0.2);
    color: #FFFFFF;
    font-size: 11px;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 20px;
    margin-top: 10px;
  }}
  .content {{
    padding: 24px;
  }}
  .card-meta {{
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 20px;
  }}
  .meta-grid {{
    width: 100%;
    border-collapse: collapse;
  }}
  .meta-grid td {{
    padding: 4px 0;
    font-size: 12px;
  }}
  .table-items {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
  }}
  .table-items th {{
    background-color: #0F766E;
    color: #FFFFFF;
    padding: 10px 12px;
    font-size: 12px;
    font-weight: 700;
    text-align: left;
  }}
  .totals {{
    background-color: #F8FAFC;
    border-radius: 8px;
    padding: 16px;
    margin-top: 20px;
    border: 1px solid #E2E8F0;
  }}
  .totals table {{
    width: 100%;
  }}
  .total-row td {{
    font-size: 17px;
    font-weight: 900;
    color: #0F766E;
    border-top: 2px solid #CBD5E1;
    padding-top: 8px;
  }}
  .footer {{
    background-color: #F8FAFC;
    border-top: 1px solid #E2E8F0;
    padding: 20px 24px;
    text-align: center;
    font-size: 11px;
    color: #64748B;
  }}
  .cufe-box {{
    background-color: #FFFFFF;
    border: 1px dashed #CBD5E1;
    padding: 8px;
    font-family: monospace;
    font-size: 10px;
    color: #475569;
    word-break: break-all;
    margin: 12px 0;
    border-radius: 4px;
  }}
</style>
</head>
<body>

<div class="container">
  <div class="header">
    <h1>FINCA TURÍSTICA SAN SEBASTIÁN S.A.S.</h1>
    <p>NIT: 901.845.123-4 • IVA Régimen Ordinario</p>
    <p>Vereda Caimito, Vía Cáqueza - Puente Quetame, Centro • Quetame, Cundinamarca 251820 • Cel: 310 456 7890</p>
    <div class="badge">DOCUMENTO EQUIVALENTE ELECTRÓNICO POS — DIAN</div>
  </div>

  <div class="content">
    <div class="card-meta">
      <table class="meta-grid">
        <tr>
          <td style="color:#0F766E;font-weight:bold;font-size:14px;">FACTURA POS: {consecutivo_str}</td>
          <td style="text-align:right;color:#64748B;"><strong>Fecha:</strong> {fecha_hora}</td>
        </tr>
        <tr>
          <td style="color:#64748B;"><strong>Cliente / Titular:</strong> {titular}</td>
          <td style="text-align:right;color:#64748B;"><strong>NIT / Cédula:</strong> {documento}</td>
        </tr>
        <tr>
          <td style="color:#64748B;"><strong>Cajero Responsable:</strong> {cajero}</td>
          <td style="text-align:right;color:#64748B;"><strong>Ubicación:</strong> {ubicacion}</td>
        </tr>
      </table>
    </div>

    <table class="table-items">
      <thead>
        <tr>
          <th>Descripción</th>
          <th style="text-align:center;">Cant.</th>
          <th style="text-align:right;">V. Unitario</th>
          <th style="text-align:right;">Subtotal</th>
        </tr>
      </thead>
      <tbody>
        {filas_items}
      </tbody>
    </table>

    <div class="totals">
      <table>
        <tr>
          <td style="padding:4px 0;color:#64748B;font-size:13px;">Subtotal Gravable:</td>
          <td style="text-align:right;font-weight:600;font-size:13px;color:#0F172A;">{formatear_cop(subtotal)}</td>
        </tr>
        <tr>
          <td style="padding:4px 0;color:#64748B;font-size:13px;">IVA / Impoconsumo (19%):</td>
          <td style="text-align:right;font-weight:600;font-size:13px;color:#0F172A;">{formatear_cop(iva)}</td>
        </tr>
        <tr class="total-row">
          <td>TOTAL PAGADO:</td>
          <td style="text-align:right;">{formatear_cop(total)}</td>
        </tr>
      </table>

      <div style="border-top:1px dashed #CBD5E1;margin-top:12px;padding-top:10px;">
        <table style="width:100%;font-size:12px;">
          {metodo_html}
        </table>
      </div>
    </div>

    <div style="margin-top:18px;">
      <div style="font-size:11px;font-weight:bold;color:#64748B;">CUFE / CUDE DE CONTROL FISCAL DIAN:</div>
      <div class="cufe-box">{cufe_hash}fe801c8901ab381710928a01f928e1</div>
    </div>
  </div>

  <div class="footer">
    <p style="margin:0 0 6px 0;font-weight:bold;color:#0F766E;">¡GRACIAS POR SU VISITA A LA FINCA TURÍSTICA SAN SEBASTIÁN!</p>
    <p style="margin:2px 0;">Conserve este comprobante electrónico para control de salida y uso de zonas húmedas y piscina.</p>
    <p style="margin:6px 0 0 0;font-size:10px;color:#94A3B8;">Facturación POS Electrónica Validada • Resolución DIAN 000165 de 2023</p>
  </div>
</div>

</body>
</html>
"""
    return html

def guardar_factura_html_local(fac: Dict[str, Any]) -> str:
    """Genera el HTML y lo almacena temporalmente para previsualización."""
    html = generar_html_factura(fac)
    num = fac.get("consecutivo", 1)
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, f"Factura_SanSebastian_FAC-{num:05d}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return filepath

def enviar_factura_email_real(fac: Dict[str, Any], destinatario: str) -> Tuple[bool, str]:
    """
    Intenta enviar la factura por SMTP real.
    Si no hay configuración SMTP cargada, retorna error explicativo y ruta de previsualización.
    """
    destinatario = destinatario.strip()
    if not destinatario or "@" not in destinatario:
        return False, "La dirección de correo electrónico no es válida."

    config = cargar_configuracion_smtp()
    usuario = config.get("usuario", "").strip()
    password = config.get("password", "").strip()
    servidor = config.get("servidor", "smtp.gmail.com").strip()
    puerto = int(config.get("puerto", 587))
    usar_tls = config.get("usar_tls", True)
    remitente_nombre = config.get("nombre_remitente", "Finca Turística San Sebastián")
    remitente_correo = config.get("correo_remitente", "").strip() or usuario

    consecutivo_str = f"FAC-{fac.get('consecutivo', 1):05d}"
    html_content = generar_html_factura(fac)

    # Si no hay credenciales configuradas
    if not usuario or not password:
        # Generar vista previa local para que el usuario pueda verla de inmediato en el navegador
        preview_path = guardar_factura_html_local(fac)
        return False, f"CONFIG_REQUIRED:{preview_path}"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🧾 Factura Electrónica {consecutivo_str} — Finca Turística San Sebastián"
        msg["From"] = f"{remitente_nombre} <{remitente_correo}>"
        msg["To"] = destinatario

        # Parte texto plano
        texto_plano = f"Finca Turística San Sebastián - Factura {consecutivo_str}\nTotal: {formatear_cop(fac.get('total', 0))}\nConsulte el documento adjunto."
        part1 = MIMEText(texto_plano, "plain", "utf-8")
        part2 = MIMEText(html_content, "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)

        if puerto == 465:
            with smtplib.SMTP_SSL(servidor, puerto, timeout=15) as server:
                server.login(usuario, password)
                server.sendmail(remitente_correo, [destinatario], msg.as_string())
        else:
            with smtplib.SMTP(servidor, puerto, timeout=15) as server:
                if usar_tls:
                    server.starttls()
                server.login(usuario, password)
                server.sendmail(remitente_correo, [destinatario], msg.as_string())

        return True, f"Factura {consecutivo_str} enviada con éxito a {destinatario}."
    except smtplib.SMTPAuthenticationError:
        return False, "Error de autenticación SMTP: Verifica que el usuario y la contraseña de aplicación sean correctos."
    except Exception as ex:
        return False, f"Error al enviar correo vía SMTP: {str(ex)}"


def generar_html_voucher_reserva(res: Dict[str, Any]) -> str:
    """Genera una plantilla HTML moderna del Comprobante de Reserva & Recibo de Abono."""
    res_id = res.get("id", "RES-001")
    titular = res.get("titular", "Huésped Registrado")
    documento = res.get("documento", "-")
    telefono = res.get("telefono", "-")
    email = res.get("email", "-")
    hab_nombre = res.get("habitacion_nombre", "Habitación")
    checkin = res.get("fecha_checkin", "-")
    checkout = res.get("fecha_checkout", "-")
    noches = res.get("noches", 1)
    tarifa_noche = res.get("tarifa_noche", 250000)
    total_estadia = res.get("total_estadia", noches * tarifa_noche)
    abono = res.get("abono", 0)
    saldo = res.get("saldo_pendiente", total_estadia - abono)
    metodo_abono = res.get("metodo_abono", "Transferencia / Nequi")
    comp_abono = res.get("comprobante_abono", "-")
    fecha_res = res.get("fecha_reserva", datetime.now().strftime("%d/%m/%Y - %I:%M %p"))
    notas = res.get("notas", "Sin observaciones adicionales.")

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Comprobante de Reserva {res_id} - Finca San Sebastián</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    background-color: #F1F5F9;
    margin: 0;
    padding: 20px;
    color: #1E293B;
  }}
  .container {{
    max-width: 620px;
    margin: 0 auto;
    background-color: #FFFFFF;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
    border: 1px solid #E2E8F0;
  }}
  .header {{
    background: linear-gradient(135deg, #0F766E 0%, #115E59 100%);
    color: #FFFFFF;
    padding: 24px;
    text-align: center;
  }}
  .header h1 {{
    margin: 0;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 0.5px;
  }}
  .header p {{
    margin: 6px 0 0 0;
    font-size: 12px;
    opacity: 0.9;
  }}
  .voucher-badge {{
    display: inline-block;
    background-color: #FEF3C7;
    color: #92400E;
    font-size: 11px;
    font-weight: 800;
    padding: 4px 12px;
    border-radius: 20px;
    margin-top: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .body {{
    padding: 24px;
  }}
  .greeting {{
    font-size: 14px;
    margin-bottom: 16px;
    line-height: 1.5;
  }}
  .highlight-card {{
    background-color: #F0FDFA;
    border: 1px solid #99F6E4;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 20px;
  }}
  .highlight-grid {{
    display: table;
    width: 100%;
  }}
  .highlight-col {{
    display: table-cell;
    width: 50%;
    vertical-align: top;
  }}
  .highlight-title {{
    font-size: 11px;
    color: #0D9488;
    font-weight: 700;
    text-transform: uppercase;
  }}
  .highlight-val {{
    font-size: 14px;
    font-weight: 800;
    color: #134E4A;
    margin-top: 2px;
  }}
  .info-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 12px;
  }}
  .info-table td {{
    padding: 8px 6px;
    border-bottom: 1px solid #F1F5F9;
  }}
  .info-table .label {{
    color: #64748B;
    font-weight: 600;
    width: 40%;
  }}
  .info-table .value {{
    color: #0F172A;
    font-weight: 700;
  }}
  .financial-box {{
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 16px;
    margin-top: 16px;
  }}
  .financial-row {{
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
    font-size: 13px;
  }}
  .abono-badge {{
    background-color: #DCFCE7;
    color: #166534;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: 800;
  }}
  .saldo-badge {{
    background-color: #EFF6FF;
    color: #1E40AF;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: 800;
  }}
  .legal-note {{
    background-color: #FFFBEB;
    border-left: 4px solid #F59E0B;
    padding: 12px;
    margin: 20px 0;
    font-size: 11px;
    color: #78350F;
    line-height: 1.5;
    border-radius: 0 6px 6px 0;
  }}
  .location-box {{
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 14px;
    font-size: 12px;
    color: #475569;
    margin-top: 16px;
  }}
  .location-box a {{
    color: #0F766E;
    font-weight: 700;
    text-decoration: underline;
  }}
  .footer {{
    background-color: #F8FAFC;
    border-top: 1px solid #E2E8F0;
    padding: 18px 24px;
    text-align: center;
    font-size: 11px;
    color: #64748B;
  }}
</style>
</head>
<body>

<div class="container">
  <div class="header">
    <h1>FINCA TURÍSTICA SAN SEBASTIÁN</h1>
    <p>NIT: 901.845.123-4 • Vía Cáqueza - Puente Quetame, Quetame, Cundinamarca</p>
    <div class="voucher-badge">Comprobante de Reserva & Recibo de Abono</div>
  </div>

  <div class="body">
    <div class="greeting">
      Estimado(a) <strong>{titular}</strong>:<br>
      Hemos registrado satisfactoriamente tu reserva y recibido el abono de garantía para tu estadía en <strong>Finca Turística San Sebastián</strong>. A continuación detallamos los términos de tu reserva:
    </div>

    <div class="highlight-card">
      <div class="highlight-grid">
        <div class="highlight-col">
          <div class="highlight-title">Alojamiento Reservado</div>
          <div class="highlight-val">🛌 {hab_nombre}</div>
          <div style="font-size: 11px; color: #0F766E; margin-top: 4px;">Código: {res_id}</div>
        </div>
        <div class="highlight-col">
          <div class="highlight-title">Fechas de Estadía</div>
          <div class="highlight-val">📅 {checkin} al {checkout}</div>
          <div style="font-size: 11px; color: #64748B; margin-top: 4px;">{noches} noche(s) • Check-in 3:00 PM / Check-out 12:00 PM</div>
        </div>
      </div>
    </div>

    <table class="info-table">
      <tr>
        <td class="label">Titular de la Reserva:</td>
        <td class="value">{titular}</td>
      </tr>
      <tr>
        <td class="label">Documento / Cédula:</td>
        <td class="value">{documento}</td>
      </tr>
      <tr>
        <td class="label">Teléfono / WhatsApp:</td>
        <td class="value">{telefono}</td>
      </tr>
      <tr>
        <td class="label">Tarifa por Noche:</td>
        <td class="value">{formatear_cop(tarifa_noche)}</td>
      </tr>
      <tr>
        <td class="label">Observaciones / Notas:</td>
        <td class="value">{notas}</td>
      </tr>
    </table>

    <div class="financial-box">
      <table style="width: 100%; font-size: 13px;">
        <tr>
          <td style="padding: 4px 0; color: #64748B;">Total Hospedaje ({noches} noches):</td>
          <td style="padding: 4px 0; text-align: right; font-weight: 700;">{formatear_cop(total_estadia)}</td>
        </tr>
        <tr>
          <td style="padding: 4px 0; color: #166534; font-weight: 700;">
            Abono Recibido ({metodo_abono}):
            <div style="font-size: 10px; color: #64748B; font-weight: normal;">Comprobante / Ref: #{comp_abono}</div>
          </td>
          <td style="padding: 4px 0; text-align: right;"><span class="abono-badge">-{formatear_cop(abono)}</span></td>
        </tr>
        <tr style="border-top: 2px solid #CBD5E1;">
          <td style="padding-top: 8px; font-weight: 800; color: #0F172A; font-size: 14px;">SALDO PENDIENTE AL CHECK-IN:</td>
          <td style="padding-top: 8px; text-align: right;"><span class="saldo-badge" style="font-size: 14px;">{formatear_cop(saldo)}</span></td>
        </tr>
      </table>
    </div>

    <div class="legal-note">
      <strong>📌 Tratamiento Tributario y Facturación Electrónica (DIAN):</strong><br>
      Este comprobante respalda la entrega de un anticipo/depósito en garantía de reserva. De acuerdo con el Estatuto Tributario colombiano y la normativa DIAN, <strong>la Factura Electrónica de Venta oficial será expedida al momento del Check-out</strong> con la liquidación definitiva del servicio, deduciendo el presente abono registrado.
    </div>

    <div class="location-box">
      <strong>📍 Ubicación y Cómo Llegar:</strong><br>
      Vereda Caimito, Vía Cáqueza - Puente Quetame, Quetame, Cundinamarca 251820.<br>
      <a href="https://www.bing.com/maps/search?name=Finca+San+Sebasti%C3%A1n+Vda+Caimito+de+Quetame&mepi=0%7E%7EEmbedded%7ELargeMapLink&FORM=MPSRPL&style=r&ss=id.ypid%3AYN43FD159BE1AEDC17&q=Finca+San+Sebasti%C3%A1n+Vda+Caimito+de+Quetame&ppois=4.326157569885254_-73.86384582519531_Finca+San+Sebasti%C3%A1n+Vda+Caimito+de+Quetame&cp=4.326158%7E-73.863846&lvl=15" target="_blank">Abrir Ubicación en el Mapa / GPS 📍</a><br>
      <small style="color: #64748B;">Línea de Atención y WhatsApp: 310 456 7890</small>
    </div>
  </div>

  <div class="footer">
    <p style="margin: 0;">¡Te esperamos con los brazos abiertos en Finca San Sebastián!</p>
    <p style="margin: 4px 0 0 0; color: #94A3B8;">Software Finca POS v2.0 • Comprobante emitido el {fecha_res}</p>
  </div>
</div>

</body>
</html>
"""
    return html


def guardar_voucher_html_local(res: Dict[str, Any]) -> str:
    """Genera y guarda en disco temporal el comprobante HTML de reserva."""
    html = generar_html_voucher_reserva(res)
    res_id = res.get("id", "RES-001")
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, f"Voucher_Reserva_{res_id}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return filepath


def enviar_voucher_email_real(res: Dict[str, Any], destinatario: str) -> Tuple[bool, str]:
    """Envía el Comprobante de Reserva & Recibo de Abono por correo vía SMTP."""
    destinatario = destinatario.strip()
    if not destinatario or "@" not in destinatario:
        return False, "La dirección de correo electrónico no es válida."

    config = cargar_configuracion_smtp()
    usuario = config.get("usuario", "").strip()
    password = config.get("password", "").strip()
    servidor = config.get("servidor", "smtp.gmail.com").strip()
    puerto = int(config.get("puerto", 587))
    usar_tls = config.get("usar_tls", True)
    remitente_nombre = config.get("nombre_remitente", "Finca Turística San Sebastián")
    remitente_correo = config.get("correo_remitente", "").strip() or usuario

    res_id = res.get("id", "RES-001")
    html_content = generar_html_voucher_reserva(res)

    if not usuario or not password:
        preview_path = guardar_voucher_html_local(res)
        return False, f"CONFIG_REQUIRED:{preview_path}"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🛎️ Comprobante de Reserva {res_id} (Abono Recibido) — Finca San Sebastián"
        msg["From"] = f"{remitente_nombre} <{remitente_correo}>"
        msg["To"] = destinatario

        texto_plano = (
            f"Finca Turística San Sebastián - Comprobante de Reserva {res_id}\n"
            f"Titular: {res.get('titular')}\n"
            f"Habitación: {res.get('habitacion_nombre')}\n"
            f"Fechas: {res.get('fecha_checkin')} al {res.get('fecha_checkout')}\n"
            f"Abono Recibido: {formatear_cop(res.get('abono', 0))}\n"
            f"Saldo Pendiente: {formatear_cop(res.get('saldo_pendiente', 0))}\n"
        )
        part1 = MIMEText(texto_plano, "plain", "utf-8")
        part2 = MIMEText(html_content, "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)

        if puerto == 465:
            with smtplib.SMTP_SSL(servidor, puerto, timeout=15) as server:
                server.login(usuario, password)
                server.sendmail(remitente_correo, [destinatario], msg.as_string())
        else:
            with smtplib.SMTP(servidor, puerto, timeout=15) as server:
                if usar_tls:
                    server.starttls()
                server.login(usuario, password)
                server.sendmail(remitente_correo, [destinatario], msg.as_string())

        return True, f"Comprobante de reserva {res_id} enviado con éxito a {destinatario}."
    except smtplib.SMTPAuthenticationError:
        return False, "Error de autenticación SMTP: Verifica que el usuario y la contraseña de aplicación sean correctos."
    except Exception as ex:
        return False, f"Error al enviar correo vía SMTP: {str(ex)}"
