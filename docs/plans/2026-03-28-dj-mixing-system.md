# 🎧 Sistema de Mezcla DJ — Diseño Integral (Opción C: IA Hybrid)

> **Fecha:** 2026-03-28  
> **Integra:** Items #5 (Espectrograma), #6 (Camelot), #7 (Demucs) del [plan de arquitectura original](./2026-03-27-architecture-design.md)

---

## 1. Visión

Convertir Sinapsis Audio Core de un **explorador** de librería a un **instrumento de mezcla profesional asistido por IA**, capaz de:
- Mezclar 2 tracks simultáneamente con crossfader, EQ y efectos
- Sincronizar BPM y tonalidad de forma automática o manual
- Sugerir transiciones inteligentes basadas en análisis acústico
- Separar stems para pre-escucha y mezcla selectiva
- Generar sets automáticos completos

---

## 2. Arquitectura del Motor de Audio

### Grafo Web Audio API (por deck)

```
[AudioBuffer/MediaElement]
        │
  ┌─────▼─────┐
  │ SoundTouch │ ←── Pitch shift / Time stretch (WASM)
  │  Worklet   │
  └─────┬─────┘
        │
  ┌─────▼─────┐
  │  3-Band EQ │ ←── BiquadFilter × 3 (low/mid/high)
  └─────┬─────┘
        │
  ┌─────▼─────┐
  │  FX Chain  │ ←── Reverb / Delay / Filter / Flanger
  └─────┬─────┘
        │
  ┌─────▼─────┐
  │  GainNode  │ ←── Volumen del deck
  └─────┬─────┘
        │
        ▼
  ╔═════════════╗
  ║  CROSSFADER  ║ ←── Equal-power crossfade (cos/sin)
  ║  GainA×GainB ║
  ╚══════┬══════╝
         │
   ┌─────▼─────┐
   │  Master    │ ←── Limiter + AnalyserNode (VU meters)
   └─────┬─────┘
         │
    🔊 Speakers
```

### Componentes Clave del Motor

| Componente | Tecnología | Propósito |
|---|---|---|
| **AudioContext** | Web Audio API nativo | Contexto maestro compartido |
| **Time Stretch** | `@soundtouchjs/audio-worklet` (WASM) | Cambiar tempo sin alterar pitch |
| **Pitch Shift** | `@soundtouchjs/audio-worklet` (WASM) | Cambiar pitch sin alterar tempo |
| **EQ 3 bandas** | `BiquadFilterNode` × 3 | lowshelf (200Hz), peaking (2kHz), highshelf (4kHz) |
| **Efectos** | `ConvolverNode` + `DelayNode` + `BiquadFilterNode` | Reverb, delay, filter sweep |
| **Crossfader** | 2 × `GainNode` con curva cos/sin | Transición suave entre decks |
| **Metering** | `AnalyserNode` | VU meters + espectrograma en tiempo real |
| **Waveforms** | wavesurfer.js × 2 instancias | Visualización + seeking por deck |

---

## 3. Nuevos Componentes Frontend

### 3.1 Vista Principal: MixConsole

```
┌──────────────────────────────────────────────────────┐
│  NEBULA MIX CONSOLE                                  │
├──────────┬───────────────────────────────┬────────────┤
│          │    DECK A     │    DECK B     │            │
│          │ ═══════════   │  ═══════════  │            │
│  Track   │ [Waveform A]  │ [Waveform B]  │  Track     │
│  Browser │ BPM: 128      │ BPM: 126      │  Suggest   │
│          │ Key: 8A       │ Key: 8A  ✓    │  (IA)      │
│  (Lista  │               │               │            │
│   con    │ ──EQ──        │ ──EQ──        │  Camelot   │
│   filtros)│ L ▓░░ M ▓▓░ H ▓▓▓│ L ▓▓░ M ▓░░ H ▓▓░│  Wheel    │
│          │               │               │            │
│          │   [FX: Rev|Dly|Flt]  [FX]     │            │
│          │               │               │            │
│          │     ◄═══════════════►          │            │
│          │        CROSSFADER              │            │
│          │                               │            │
│          │  [▶Cue1] [▶Cue2] [▶Cue3]    │            │
├──────────┴───────────────────────────────┴────────────┤
│  [SYNC] [MASTER TEMPO] [AUTO-MIX]  VU: ▓▓▓▓▓░░░     │
└──────────────────────────────────────────────────────┘
```

### 3.2 Componentes Nuevos

| Componente | Archivo | Descripción |
|---|---|---|
| **MixConsole.vue** | `components/mixing/MixConsole.vue` | Layout principal de mezcla |
| **DeckPlayer.vue** | `components/mixing/DeckPlayer.vue` | Un deck completo (waveform + controles + EQ) |
| **Crossfader.vue** | `components/mixing/Crossfader.vue` | Slider horizontal con curva equal-power |
| **EQKnobs.vue** | `components/mixing/EQKnobs.vue` | 3 knobs rotativos (Low/Mid/High) |
| **FXRack.vue** | `components/mixing/FXRack.vue` | Panel de efectos (reverb, delay, filter, flanger) |
| **BPMSync.vue** | `components/mixing/BPMSync.vue` | Controles de sync + pitch slider |
| **VUMeter.vue** | `components/mixing/VUMeter.vue` | Medidor de niveles LED-style |
| **CamelotWheel.vue** | `components/mixing/CamelotWheel.vue` | Rueda de compatibilidad armónica visual |
| **TrackSuggest.vue** | `components/mixing/TrackSuggest.vue` | Panel IA de sugerencias de siguiente track |
| **HotCues.vue** | `components/mixing/HotCues.vue` | Botones de cue points + loops |
| **Spectrogram.vue** | `components/mixing/Spectrogram.vue` | Espectrograma en tiempo real por deck |

### 3.3 Servicio de Audio (Composable)

```
composables/
  useAudioEngine.ts   ← Singleton del AudioContext + routing
  useDeck.ts          ← Estado y controles por deck
  useCrossfader.ts    ← Lógica de crossfade equal-power
  useEffects.ts       ← Cadena de FX configurable
  useBPMSync.ts       ← Sync automático de tempo
  useMixSuggestions.ts ← Motor de sugerencias IA
```

---

## 4. Backend: Nuevos Endpoints

### 4.1 Stems (Demucs)

| Endpoint | Método | Descripción |
|---|---|---|
| `POST /stems/{filename}` | POST | Separa track en 4 stems (vocals, drums, bass, other) |
| `GET /stems/{filename}/{stem}` | GET | Stream de un stem individual |
| `GET /stems/{filename}/status` | GET | Estado de procesamiento |

### 4.2 Análisis Extendido

| Endpoint | Método | Descripción |
|---|---|---|
| `GET /tracks/{filename}/beatgrid` | GET | Posiciones de beats (en segundos) |
| `GET /tracks/{filename}/segments` | GET | Segmentos detectados (intro, build, drop, break, outro) |
| `GET /mix/suggest?current={filename}` | GET | Top 10 tracks compatibles por key+bpm+energy |

### 4.3 Nuevos Servicios Backend

```
services/
  stems_service.py        ← Integración con Demucs (Meta)
  beatgrid_service.py     ← Detección de beats con librosa.beat
  segment_service.py      ← Detección de secciones (intro/drop/outro)
  mix_suggest_service.py  ← Motor Camelot + proximity scoring
```

---

## 5. Motor de Sugerencias IA (Camelot + Scoring)

### 5.1 Camelot Wheel — Compatibilidad Armónica

```
       1A ←→ 1B
      / \      
    12A   2A   
   / \   / \   
  11A  ...  3A  
   ...       ...
```

**Reglas de compatibilidad:**
- ✅ **Misma posición** (8A → 8A): Perfecto
- ✅ **±1 posición** (8A → 7A, 9A): Suave
- ✅ **Cambio A↔B** (8A → 8B): Mood shift
- ⚠️ **±2 posiciones**: Posible con cuidado
- ❌ **Más de ±2**: Clash armónico

### 5.2 Score de Compatibilidad

```python
def compute_mix_score(current, candidate):
    # Key compatibility (0-100)
    key_score = camelot_distance(current.key, candidate.key) * 40
    
    # BPM proximity (0-100), penalizar si diff > 6%
    bpm_diff = abs(current.bpm - candidate.bpm) / current.bpm
    bpm_score = max(0, (1 - bpm_diff / 0.08)) * 30
    
    # Energy flow (0-100), preferir transiciones suaves
    energy_diff = abs(current.energy - candidate.energy)
    energy_score = max(0, (1 - energy_diff / 0.5)) * 20
    
    # Timbral similarity via MFCC distance
    mfcc_score = (1 - mfcc_distance(current, candidate)) * 10
    
    return key_score + bpm_score + energy_score + mfcc_score
```

---

## 6. Detección de Segmentos (Auto-Mix Points)

El backend analizará cada track para detectar secciones:

| Segmento | Detección | Uso en mezcla |
|---|---|---|
| **Intro** | Primeros N beats con energy < 30% promedio | Punto ideal de entrada |
| **Build-up** | Energy creciente + onset rate creciente | Tensión, preparar transición |
| **Drop** | Pico súbito de energy + spectral contrast | Impacto, alinear con otro drop |
| **Break** | Caída de energy post-drop | Punto de mezcla (bajar bass) |
| **Outro** | Últimos N beats con energy descendiente | Punto ideal de salida |

```python
# librosa segmentation
segments = librosa.segment.agglomerative(mfcc, k=6)
boundaries = librosa.segment.detect(onset_envelope, sr)
```

---

## 7. Fases de Implementación

### Fase 1: Motor de Audio Dual (1-2 semanas)
- [ ] Composable `useAudioEngine` con AudioContext compartido
- [ ] Composable `useDeck` con GainNode + BiquadFilter EQ
- [ ] `DeckPlayer.vue` con wavesurfer.js + controles de transporte
- [ ] `Crossfader.vue` con curva equal-power
- [ ] `VUMeter.vue` con AnalyserNode
- [ ] Vista `MixConsole.vue` con layout dual

### Fase 2: Sync + Effects (1-2 semanas)
- [ ] Instalar `@soundtouchjs/audio-worklet` para pitch/tempo
- [ ] `BPMSync.vue` — botón SYNC que ajusta playbackRate
- [ ] `EQKnobs.vue` — knobs rotativos SVG con BiquadFilter
- [ ] `FXRack.vue` — reverb (ConvolverNode), delay, filter sweep
- [ ] `HotCues.vue` — set/jump cue points
- [ ] `Spectrogram.vue` — vista de frecuencias en tiempo real

### Fase 3: Backend IA (1-2 semanas)
- [ ] `beatgrid_service.py` — detección de beats por track
- [ ] `segment_service.py` — detección de intro/drop/outro
- [ ] `mix_suggest_service.py` — scoring Camelot + BPM + energy
- [ ] Endpoints REST: `/mix/suggest`, `/tracks/{id}/beatgrid`, `/tracks/{id}/segments`
- [ ] `CamelotWheel.vue` — visualización de compatibilidad
- [ ] `TrackSuggest.vue` — panel de recomendaciones

### Fase 4: Stems + Auto-Mix (2-3 semanas)
- [ ] Integrar Demucs en backend (docker/local)
- [ ] `stems_service.py` — separación + almacenamiento
- [ ] Endpoints: `POST /stems/{id}`, `GET /stems/{id}/{stem}`
- [ ] UI de stems en cada deck (4 faders: vocals/drums/bass/other)
- [ ] Auto-mix engine: generar transiciones basadas en segmentos
- [ ] Modo "Auto DJ" — genera un set continuo

---

## 8. Dependencias Nuevas

### Frontend (npm/bun)
```
@soundtouchjs/audio-worklet    # Time stretch / pitch shift WASM
```

### Backend (poetry)
```
demucs                          # Separación de stems
librosa                         # Ya instalado — beat detection + segmentation
```

> **Nota:** No se necesita Tone.js. El Web Audio API nativo con BiquadFilterNode + ConvolverNode + DelayNode cubre todos los efectos necesarios sin agregar una dependencia pesada.

---

## 9. Integración con Arquitectura Existente

| Item del plan original | Integración en mezcla |
|---|---|
| #5 Espectrograma | → `Spectrogram.vue` por deck en MixConsole |
| #6 Motor Camelot | → `CamelotWheel.vue` + `mix_suggest_service.py` |
| #7 Separación Stems | → `stems_service.py` + faders por stem en cada deck |
| Nebula Console 3D | Se mantiene como vista de exploración. MixConsole es una **nueva vista** |
| Filtros/navegación | Track Browser en MixConsole reutiliza la misma lógica de filtros |

---

## 10. Diseño Visual (Nebula Mix Console)

- **Fondo:** Mismo gradiente nebula oscuro (`#09090b`) con blobs sutiles
- **Decks:** Paneles glassmorphism con bordes cyan (Deck A) y magenta (Deck B)
- **Crossfader:** Slider horizontal con glow gradient cyan↔magenta
- **Knobs EQ:** SVG rotativos con sombra neon del color del deck
- **VU Meters:** Barras LED verticales estilo hardware (verde→amarillo→rojo)
- **Camelot Wheel:** Círculo SVG interactivo con arcos coloreados
- **Waveforms:** Multicolor como el player actual, pero con beat markers
