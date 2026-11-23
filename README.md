# 🌌 ID System — Inteligencia Musical y Cartografía de Audio

> **Parte del [Diegod Sound Engine](https://juand2g.entrelaniebla.org)** — el "cerebro" del ecosistema.

Plataforma de análisis de audio, catalogación e indexación espacial 3D. Escanea librerías de música local, extrae características acústicas con procesamiento digital de señales, y visualiza canciones como nodos en un universo 3D según sus similitudes matemáticas.

## 🏗️ Arquitectura

```
┌────────────────────┐    ┌────────────────────┐    ┌──────────────┐
│   Frontend (Nuxt)  │◄──►│  Backend (FastAPI)  │◄──►│  MongoDB 6.0 │
│   :3000            │    │   :8000             │    │  :27018      │
│                    │    │                     │    │  (Docker)    │
│ • SonicGalaxy 3D   │    │ • Scanner + librosa │    └──────────────┘
│ • WaveformPlayer   │    │ • UMAP coordinates  │
│ • Camelot Wheel    │    │ • Streaming audio   │
└────────────────────┘    └────────────────────┘
```

| Capa | Tecnología |
|:-----|:-----------|
| Backend | Python 3.12, FastAPI, Poetry, Uvicorn |
| Frontend | Nuxt 3, Vue 3, TresJS, Three.js, TailwindCSS |
| BD | MongoDB 6.0 (Docker, puerto 27018) |
| Audio | librosa, scikit-learn, UMAP, mutagen |

## 📡 API Endpoints

| Método | Ruta | Descripción |
|:-------|:-----|:------------|
| `POST` | `/scan` | Escanea la librería musical y extrae features |
| `POST` | `/rescan-metadata` | Re-lee metadatos de tracks con título/artista Unknown |
| `POST` | `/rescan-bpm-key` | Normaliza BPM y detecta key para todos los tracks |
| `GET` | `/tracks` | Lista paginada de tracks analizados |
| `GET` | `/tracks/{filename}` | Track específico por nombre de archivo |
| `GET` | `/stream/{filename}` | Streaming de audio para reproducción en el frontend |
| `POST` | `/map/generate` | Calcula coordenadas UMAP 3D para la Sonic Galaxy |

## 🚀 Ejecución Local

### Requisitos
- Docker y Docker Compose
- Python 3.12 + Poetry
- Node.js + Bun (o npm)

### Paso 1: Levantar MongoDB
```bash
cd ~/Música/ID
docker compose up -d
```

### Paso 2: Backend
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API documentada en: http://localhost:8000/docs

### Paso 3: Frontend
```bash
cd frontend
bun install
bun run dev
```
Interfaz web en: http://localhost:3000

### Paso 4: Poblar datos
1. Abre http://localhost:8000/docs
2. Ejecuta `POST /scan` — escanea tu librería musical
3. Ejecuta `POST /map/generate` — calcula las coordenadas 3D
4. Recarga http://localhost:3000 — verás los nodos en la galaxia

## ⚙️ Configuración

### Variables de entorno (backend/app/config.py)
| Variable | Default | Descripción |
|:---------|:--------|:------------|
| `LIBRARY_PATH` | `/home/juand2g/Música/music` | Ruta a la librería musical |
| `MONGO_URI` | `mongodb://admin:password123@127.0.0.1:27018/...` | Conexión MongoDB |

## 📁 Estructura
```
ID/
├── docker-compose.yml          # MongoDB container
├── backend/
│   ├── pyproject.toml          # Dependencias (Poetry)
│   └── app/
│       ├── main.py             # FastAPI bootstrap
│       ├── config.py           # Configuración centralizada
│       ├── database.py         # Conexión MongoDB
│       ├── core/
│       │   ├── audio_processor.py   # Extracción de features + metadatos
│       │   └── cartography.py       # Algoritmo UMAP
│       ├── routers/
│       │   ├── scan.py         # Endpoints de escaneo
│       │   ├── tracks.py       # Consulta + streaming
│       │   └── analysis.py     # Generación de mapa UMAP
│       └── services/
│           ├── scanner_service.py      # Lógica de escaneo
│           ├── cartography_service.py  # Cálculo UMAP
│           └── feature_service.py      # Procesamiento de features
└── frontend/
    ├── app/app.vue             # Componente principal
    ├── components/
    │   ├── SonicGalaxy.vue     # Visualización 3D (TresJS/Three.js)
    │   └── WaveformPlayer.vue  # Reproductor con wavesurfer.js
    └── composables/
        └── useCamelot.js       # Camelot Wheel (mezcla armónica)
```

---
Desarrollado por **juand2g** · GitLab: `gitlab.com/juand2g/id`
