# ============================================================
# Dockerfile — Multi-stage build para ProyectoFinca POS API
# ============================================================
# Etapas:
#   1. restore  — descarga NuGet packages (se cachea si no cambian .csproj)
#   2. build    — compila el código en Release
#   3. publish  — genera el artefacto final optimizado
#   4. final    — imagen mínima de runtime (~200MB vs ~600MB del SDK)
# ============================================================

# ── Etapa 1: Restore (aprovecha la caché de Docker si no cambian los .csproj) ──
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS restore
WORKDIR /src

# Copiar solo los archivos .csproj primero para aprovechar la caché de capas
COPY ["src/ProyectoFinca.API/ProyectoFinca.API.csproj",                         "src/ProyectoFinca.API/"]
COPY ["src/ProyectoFinca.Application/ProyectoFinca.Application.csproj",         "src/ProyectoFinca.Application/"]
COPY ["src/ProyectoFinca.Infrastructure/ProyectoFinca.Infrastructure.csproj",   "src/ProyectoFinca.Infrastructure/"]
COPY ["src/ProyectoFinca.Domain/ProyectoFinca.Domain.csproj",                   "src/ProyectoFinca.Domain/"]

RUN dotnet restore "src/ProyectoFinca.API/ProyectoFinca.API.csproj" --locked-mode

# ── Etapa 2: Build ──────────────────────────────────────────────────────────────
FROM restore AS build
WORKDIR /src

# Copiar todo el código fuente
COPY src/ src/

RUN dotnet build "src/ProyectoFinca.API/ProyectoFinca.API.csproj" \
    -c Release \
    -o /app/build \
    --no-restore

# ── Etapa 3: Publish ────────────────────────────────────────────────────────────
FROM build AS publish
RUN dotnet publish "src/ProyectoFinca.API/ProyectoFinca.API.csproj" \
    -c Release \
    -o /app/publish \
    --no-restore \
    /p:UseAppHost=false

# ── Etapa 4: Runtime final (imagen mínima) ──────────────────────────────────────
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS final

# Usuario no-root por seguridad (no correr como root en producción)
RUN addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --ingroup appgroup appuser

WORKDIR /app

# Puerto interno que escucha la app (Kestrel)
EXPOSE 8080

# Variables de entorno base
ENV ASPNETCORE_URLS=http://+:8080
ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=false
ENV TZ=America/Bogota

# Copiar el artefacto publicado
COPY --from=publish /app/publish .

# Cambiar al usuario no-root
USER appuser

# Punto de entrada
ENTRYPOINT ["dotnet", "ProyectoFinca.API.dll"]
