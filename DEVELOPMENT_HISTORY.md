# 📜 Historial de Desarrollo — ID System (Sinapsis Audio Core)

> **Proyecto:** Plataforma de Inteligencia Musical, Catalogación y Cartografía de Audio 3D  
> **Autor:** Juand2g  
> **Stack:** FastAPI (Python 3.12) · Nuxt 3 (Vue 3) · MongoDB 6.0 · Three.js/TresJS

---

## Fase 0 — Fundación del Proyecto

Se estableció la arquitectura base cliente-servidor:

| Componente | Tecnología | Puerto |
|---|---|---|
| Backend | Python 3.12, FastAPI, Poetry, Uvicorn | `:8000` |
| Frontend | Nuxt 3, Vue 3, TresJS, TailwindCSS | `:3000` |
| Base de Datos | MongoDB 6.0 (Docker Compose) | `:27018` |

### Módulos core implementados:
- `app/core/audio_processor.py` — Análisis espectral con `librosa` (BPM, tonalidad, features).
- `app/core/shazam_client.py` — Identificación acústica con `shazamio`.
- `app/core/cartography.py` — Reducción dimensional con `UMAP` y `scikit-learn` para mapa 3D.

### API Endpoints:
- `POST /scan` — Escaneo recursivo de la librería musical.
- `GET /tracks` — Consulta paginada del catálogo.
- `POST /identify` — Identificación de audio vía Shazam.
- `POST /map/generate` — Generación de coordenadas UMAP en background.

### Ejecución del sistema (3 terminales):
```bash
# Terminal 1: Base de datos
docker compose up -d

# Terminal 2: Backend
cd backend && poetry run uvicorn app.main:app --reload --port 8000

# Terminal 3: Frontend
cd frontend && bun run dev   # o npm run dev
```

---

## Fase 1 — Problemas Detectados y Correcciones

### 🐛 Bug 1: Lectura de metadatos ID3 (Backend — Crítico)

**Síntoma:** El generador de mapas UMAP reportaba `"Tracks procesados: 0/86"` a pesar de tener 86 canciones en la BD.

**Causa raíz:** El escáner usaba una abstracción de alto nivel (probablemente `EasyID3` de Mutagen) que no leía las etiquetas crudas `TBPM` y `TKEY`. Sin embargo, el script de prueba `inspect_tags.py` sí las detectaba al usar `ID3` directamente.

```text
--- inspect_tags.py (SÍ funciona) ---
TBPM: 150
TKEY: Am

--- Logs del servidor (FALLA) ---
INFO:app.core.cartography:Calculando mapa para 86 tracks...
INFO:app.core.cartography:Mapa actualizado. Tracks procesados: 0/86
```

**Solución propuesta:**
- Reescribir `extract_metadata` en el escáner para importar `ID3` desde `mutagen.id3`.
- Buscar explícitamente en tags crudos: `TBPM` para BPM, `TKEY` para tonalidad.
- Agregar logs de debug: `🔍 Procesado: {title} | BPM: {bpm} | Key: {key}`.

**Estado:** ⏳ Pendiente de implementación.

---

### 🐛 Bug 2: Regresión visual del Frontend

**Síntoma:** Se perdió el estilo "Cyberpunk/Glassmorphism" del input de búsqueda. La lista lateral solo mostraba nombres de canciones sin BPM/Key.

**Correcciones requeridas:**
1. Restaurar input de búsqueda con bordes translúcidos, ícono integrado y fondo oscuro.
2. En la lista `v-for`, renderizar chips/badges con `track.bpm` y `track.key`.
3. Mantener botones de "Escanear" y "Regenerar Mapa" funcionales.

**Estado:** ✅ Parcialmente implementado (el agente ayudó con ajustes visuales).

---

### 🐛 Bug 3: MongoDB `Connection refused`

**Síntoma:** Al iniciar el backend sin Docker, el error `[Errno 111] Connection refused` en puerto `27018`.

**Causa:** MongoDB corre dentro de Docker Compose. Si no se ejecuta `docker compose up -d` primero, no hay nadie escuchando en el puerto `27018`.

**Solución:** Siempre ejecutar `docker compose up -d` antes de levantar el backend.

**Conexión configurada en `main.py`:**
```python
MONGO_URI = "mongodb://<usuario>:<contraseña>@127.0.0.1:27018/?authSource=admin&directConnection=true"
```

---

## Fase 2 — Roadmap de Características (Pendientes)

### 1. 🎵 Audio Player & Waveform
- Integrar `wavesurfer.js` para reproducción y visualización de forma de onda.
- Nuevo endpoint `GET /stream/{track_id}` para streaming de audio.
- Integrarlo visualmente en la sección "Active Signal".

### 2. 🎶 Motor de Mezcla Armónica (Camelot Wheel)
- Dado un track en `Am (8A)`, resaltar tracks compatibles:
  - Mismo tono: `Am (8A)`
  - Dominante/Subdominante: `Em (9A)`, `Dm (7A)`
  - Relativo mayor: `C (8B)`
- Indicador visual en la lista lateral (punto verde / borde brillante).

### 3. ⚡ Auto-Tagging de Energía (Backend)
- Si el archivo no tiene etiqueta de energía, calcular `RMS` con Librosa (primeros 30s).
- Normalizar de 0 a 100 y guardar como `energy_level` en MongoDB.
- Mostrar valor real en la barra "Energy Level" de la UI.

---

## Notas Técnicas

### Ruta de librería musical
Actualmente hardcodeada en `backend/app/main.py` línea 43:
```python
LIBRARY_PATH = Path("/mnt/c/Users/Lenovo/Music/music")
```
> ⚠️ **Debe actualizarse** según el entorno local de cada desarrollador.

### Credenciales de MongoDB (Docker)
```yaml
MONGO_INITDB_ROOT_USERNAME: <usuario>
MONGO_INITDB_ROOT_PASSWORD: <contraseña>
```

### Dependencias clave
| Backend (Poetry) | Frontend (npm/bun) |
|---|---|
| `fastapi`, `uvicorn` | `nuxt ^4.2.2`, `vue ^3.5` |
| `librosa`, `shazamio` | `three`, `@tresjs/core` |
| `pymongo`, `mutagen` | `chart.js`, `vue-chartjs` |
| `umap-learn`, `scikit-learn` | `@nuxtjs/tailwindcss` |
