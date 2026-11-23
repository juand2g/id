# ID System — Diseño de Arquitectura v2.0

> **Fecha:** 2026-03-27  
> **Decisiones validadas por brainstorming**

---

## 1. Visión del Producto

**ID System** es un **universo musical personal** que mapea tu librería de audio a un espacio 3D navegable donde cada canción es un nodo cuyas características acústicas definen su posición, color y comportamiento. El objetivo final: construir un **genoma musical** de tus gustos para usarlo como referencia o input en generación de música.

### Pilares:
1. **Análisis profundo** — Extraer el máximo de features acústicos de cada track
2. **Universo híbrido** — UMAP para agrupación + capas interpretables (energía, mood, brillo)
3. **Reproducción inmersiva** — Waveform + espectrograma + separación de stems (Demucs)
4. **Identificación inteligente** — (Futuro) Escuchar, identificar, descargar y catalogar automáticamente

---

## 2. Arquitectura Backend (Refactor)

### Estructura actual (monolítica):
```
backend/app/
├── main.py          ← TODO está aquí (165 líneas, 5 endpoints)
└── core/
    ├── audio_processor.py
    ├── cartography.py
    └── shazam_client.py
```

### Estructura propuesta (modular por dominio):
```
backend/app/
├── main.py                    ← Solo bootstrap: CORS, lifespan, incluir routers
├── config.py                  ← Configuración centralizada (MONGO_URI, LIBRARY_PATH, etc.)
├── database.py                ← Conexión MongoDB compartida
│
├── routers/                   ← Endpoints organizados por dominio
│   ├── scan.py                ← POST /scan
│   ├── tracks.py              ← GET /tracks, GET /tracks/{id}, GET /stream/{id}
│   ├── analysis.py            ← POST /map/generate, GET /features/{id}
│   └── identify.py            ← POST /identify
│
├── services/                  ← Lógica de negocio pesada
│   ├── scanner_service.py     ← Escaneo recursivo + extracción de metadatos
│   ├── feature_service.py     ← Extracción completa de features con Librosa
│   ├── cartography_service.py ← UMAP / mapeo 3D
│   ├── stream_service.py      ← Streaming de archivos de audio
│   └── shazam_service.py      ← Identificación con ShazamIO
│
└── models/                    ← Schemas Pydantic para validación
    ├── track.py
    └── analysis.py
```

### Principios:
- **Separación de responsabilidades:** Cada router delega en su servicio correspondiente
- **Config centralizada:** Todo en `config.py` (evita hardcodear URIs en múltiples archivos)
- **Base de datos compartida:** Un solo cliente MongoDB reutilizado por todos los servicios

---

## 3. Features Acústicos a Extraer (Librosa)

### Tier 1 — Core (Obligatorio, se extrae siempre):
| Feature | Descripción | Uso en el mapa |
|---|---|---|
| **BPM** | Tempo estimado | Velocidad rítmica |
| **Key** | Tonalidad (via etiquetas ID3 o Chroma) | Compatibilidad armónica |
| **Energy (RMS)** | Volumen promedio normalizado 0-1 | Tamaño/brillo del nodo |
| **Duration** | Duración en segundos | Metadata |
| **MFCC** (13 coefs) | Textura tímbrica | Input principal para UMAP |

### Tier 2 — Espectral (Recomendado):
| Feature | Descripción | Uso en el mapa |
|---|---|---|
| **Spectral Centroid** | "Brillo" del sonido (Hz promedio) | Color del nodo (oscuro→brillante) |
| **Spectral Contrast** | Diferencia picos/valles por banda | Plenitud sonora |
| **Spectral Rolloff** | Frecuencia bajo la cual está el 85% de la energía | Oscuridad/calidez |
| **Zero Crossing Rate** | Textura percusiva vs tonal | Tipo de sonido |
| **Chroma** (12 bins) | Perfil armónico completo | Mapa de tonalidades |

### Tier 3 — Avanzado (Para ML/generación futura):
| Feature | Descripción | Uso futuro |
|---|---|---|
| **Onset Rate** | Densidad de eventos rítmicos | Complejidad rítmica |
| **Tempogram** | Variaciones de tempo | Estabilidad rítmica |
| **Danceability** | Regularidad + fuerza del beat | Clasificación |
| **Mel Spectrogram** | Representación completa frecuencia/tiempo | Entrenamiento de modelos |

---

## 4. Significado del Espacio 3D (Modelo Híbrido)

### Base: UMAP agrupa por similitud acústica
- Input: vector de todos los Tier 1 + Tier 2 features concatenados
- Output: coordenadas (x, y, z) donde tracks similares quedan cercanos

### Capas interpretables superpuestas:
| Capa visual | Feature fuente | Representación |
|---|---|---|
| **Color del nodo** | Energy (RMS) | Frío (azul/blanco) → Caliente (magenta/rojo) |
| **Tamaño del nodo** | Spectral Centroid | Pequeño (grave/oscuro) → Grande (brillante/agudo) |
| **Anillos** | BPM | Más anillos = más rápido |
| **Opacidad** | Danceability | Sólido = muy bailable, Translúcido = ambient |
| **Filtros UI** | Key, Genre, BPM range | Sliders/toggles para filtrar el universo |

---

## 5. Reproducción y Visualización (Fases)

### Fase 1 (Inmediata): Waveform + Playback
- **Frontend:** `wavesurfer.js` para renderizar la onda y controlar reproducción
- **Backend:** Endpoint `GET /stream/{track_id}` que sirve el archivo MP3/WAV
- **Visual:** Onda con cursor, colores por intensidad, controles play/pause/seek

### Fase 2 (Corto plazo): Espectrograma en tiempo real
- Plugin spectrogram de wavesurfer.js o Web Audio API con AnalyserNode
- Mapa de calor de frecuencias debajo de la waveform

### Fase 3 (Futuro): Separación de Stems con Demucs
- **Backend:** Integrar `demucs` (Meta) para separar en: vocals, drums, bass, other
- Almacenar stems en MongoDB GridFS o filesystem
- **Frontend:** Múltiples waveforms apiladas, cada una con su stem, muteable

---

## 6. Orden de Implementación

| Prioridad | Tarea | Complejidad |
|---|---|---|
| 🔴 1 | Refactor backend (routers + services + config) | Media |
| 🔴 2 | Extracción completa de features (Tier 1 + Tier 2) | Media |
| 🟡 3 | Reproductor con waveform (wavesurfer.js) | Media |
| 🟡 4 | Capas visuales interpretables en el mapa 3D | Baja |
| 🟢 5 | Espectrograma en tiempo real | Baja |
| 🟢 6 | Motor de mezcla armónica (Camelot) | Baja |
| 🔵 7 | Separación de stems (Demucs) | Alta |
| 🔵 8 | Identificación automática + descarga | Alta |

---

## 7. Stack Tecnológico Confirmado

| Capa | Tecnología |
|---|---|
| **Backend** | Python 3.12, FastAPI, Poetry |
| **Audio DSP** | Librosa, Mutagen, (futuro: Demucs) |
| **Identificación** | ShazamIO |
| **ML/Mapping** | UMAP, scikit-learn, NumPy |
| **Base de datos** | MongoDB 6.0 (Docker Compose) |
| **Frontend** | Nuxt 3, Vue 3, TailwindCSS |
| **3D Engine** | Three.js via TresJS |
| **Audio Player** | wavesurfer.js (por agregar) |
| **Infra** | Docker Compose (BD), Poetry (backend), Bun (frontend) |
