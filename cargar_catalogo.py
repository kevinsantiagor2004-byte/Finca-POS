"""Carga el catalogo comercial de Finca San Sebastian en la API.

Uso (con la API arriba):  python cargar_catalogo.py
Pide el correo y la clave del Admin. No guarda ni imprime la clave.
Es seguro repetirlo: omite lo que ya existe por nombre.
"""
import getpass, json, sys, urllib.request, urllib.error

BASE = (input("URL de la API [http://localhost:8080/api]: ").strip() or "http://localhost:8080/api").rstrip("/")

PLANES = [
    ("Pasadía Piscina Adulto", 65000, "Piscinas + Almuerzo Campestre + Acceso General"),
    ("Pasadía Piscina Niño", 45000, "Toboganes + Menú Infantil + Acceso Zona Niños"),
    ("Pasadía VIP Solarium", 90000, "Cama balinesa + Cóctel bienvenida + Almuerzo"),
    ("Noche Cabaña Pareja Jacuzzi", 250000, "Cama King, Jacuzzi privado, Desayuno campestre"),
    ("Noche Cabaña Familiar (6 Pax)", 380000, "2 habitaciones, terraza BBQ, vista piscina"),
    ("Suite Mirador Campestre", 320000, "Vista panorámica, hamacas, minibar incluido"),
]
SERVICIOS = [
    ("Limonada de Coco Cremosita", 14000, "Bebidas", "Frappé artesanal de leche de coco natural 500ml"),
    ("Balde Cerveza Corona (x5)", 58000, "Bebidas", "5 botellas en hielera con limones frescos"),
    ("Cerveza Club Colombia Dorada", 8500, "Bebidas", "Lata 330ml helada para zona húmeda"),
    ("Mojito Artesanal San Sebastián", 24000, "Bebidas", "Ron blanco, hierbabuena fresca y soda"),
    ("Piña Colada Frappé", 22000, "Bebidas", "En piña natural con sombrilla de piscina"),
    ("Agua Mineral Manantial 600ml", 4500, "Bebidas", "Agua de manantial natural sin gas"),
    ("Bandeja San Sebastián Especial", 38000, "Restaurante", "Frijoles, chicharrón, carne, huevo, maduro y aguacate"),
    ("Trucha al Ajillo con Patacón", 36000, "Restaurante", "Filete de trucha dorada al ajillo con patacón"),
    ("Costillas BBQ Ahumadas en Leña", 38000, "Restaurante", "Costillar bañado en salsa BBQ con papas"),
    ("Sancocho de Gallina Criolla", 34000, "Restaurante", "Leña tradicional, mazorca, yuca, arroz y aguacate"),
    ("Salchipapa Campestre Piscina", 22000, "Restaurante", "Papas rústicas, salchicha premium, tocineta y queso"),
    ("Hamburguesa Doble Carne Angus", 26000, "Restaurante", "Carne Angus 200g, cheddar, tocineta y papas"),
]

token = None
def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            t = r.read().decode()
            return r.status, (json.loads(t) if t else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]
    except Exception as e:
        print("No pude conectar con la API:", e); sys.exit(1)

st, d = call("POST", "/auth/login", {"email": input("Correo Admin: ").strip(), "password": getpass.getpass("Clave Admin: ")})
if st != 200:
    print("Login falló:", st); sys.exit(1)
token = d["token"]

def lista(path):
    st, d = call("GET", path)
    if isinstance(d, dict): d = d.get("items") or d.get("data") or []
    return d if st == 200 and isinstance(d, list) else []

planes = {p["nombre"]: p for p in lista("/planes")}
servs = {s["nombre"]: s for s in lista("/services")}

for n, pr, de in PLANES:
    if n not in planes:
        st, d = call("POST", "/planes", {"nombre": n, "precioBase": pr, "descripcion": de, "isActive": True})
        print("Plan", n, "->", st)
        if st in (200, 201): planes[n] = d
for n, pr, cat, de in SERVICIOS:
    if n not in servs:
        st, d = call("POST", "/services", {"nombre": n, "precioAdicional": pr, "categoria": cat, "descripcion": de, "isActive": True})
        print("Servicio", n, "->", st)
        if st in (200, 201): servs[n] = d

# Asignar como opcionales los servicios del catalogo a los 6 planes
ok = 0
for pn, _, _ in PLANES:
    p = planes.get(pn)
    if not p: continue
    ya = {x.get("nombreServicio") for x in (p.get("servicios") or [])}
    for i, (sn, _, _, _) in enumerate(SERVICIOS):
        s = servs.get(sn)
        if s and sn not in ya:
            st, _ = call("POST", f"/planes/{p['id']}/servicios", {"serviceId": s["id"], "esObligatorio": False, "ordenPresentacion": i})
            ok += st in (200, 201)
print(f"Listo. Asignaciones nuevas: {ok}")
