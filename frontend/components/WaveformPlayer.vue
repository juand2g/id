<template>
  <transition name="player-slide">
    <div v-if="track" class="fixed bottom-0 left-[320px] right-0 z-50 bg-nebula-deep/95 backdrop-blur-2xl border-t border-pulse/20 shadow-[0_-4px_30px_rgba(6,182,212,0.1)]">

      <!-- Loading bar -->
      <div v-if="isLoading" class="absolute top-0 left-0 h-[2px] bg-gradient-to-r from-pulse via-laser to-pulse animate-pulse w-full"></div>

      <div class="flex items-center gap-4 px-5 py-3">

        <!-- Play/Pause Button -->
        <button @click="togglePlay"
                class="size-11 rounded-full flex items-center justify-center bg-gradient-to-br from-pulse/20 to-laser/10 hover:from-pulse/30 hover:to-laser/20 border border-pulse/30 hover:border-pulse/50 transition-all group shrink-0 shadow-[0_0_20px_rgba(6,182,212,0.15)]">
          <span class="material-symbols-outlined text-pulse text-[22px] group-hover:scale-110 transition-transform">
            {{ isPlaying ? 'pause' : 'play_arrow' }}
          </span>
        </button>

        <!-- Track Info -->
        <div class="min-w-[140px] max-w-[180px] shrink-0">
          <p class="text-[11px] text-ink-primary font-medium truncate">{{ track.title || track.filename }}</p>
          <p class="text-[10px] text-ink-muted truncate">{{ track.artist || 'Unknown' }}</p>
        </div>

        <!-- Time (Current) -->
        <span class="text-[11px] text-pulse font-data tabular-nums w-[38px] text-right shrink-0 font-bold">
          {{ formatTime(currentTime) }}
        </span>

        <!-- Waveform Container -->
        <div class="flex-1 relative h-[48px] cursor-pointer rounded-md overflow-hidden group">
          <!-- Glow backdrop -->
          <div class="absolute inset-0 -inset-x-2 rounded-lg blur-xl opacity-30 group-hover:opacity-50 transition-opacity duration-500 pointer-events-none"
               style="background: linear-gradient(90deg, #06b6d4, #7c3aed, #c026d3, #7c3aed, #06b6d4);">
          </div>
          <!-- Waveform target (wavesurfer renders here) -->
          <div ref="waveformContainer" class="relative z-10 w-full h-full"></div>
        </div>

        <!-- Time (Duration) -->
        <span class="text-[11px] text-ink-secondary font-data tabular-nums w-[38px] shrink-0 font-medium">
          {{ formatTime(duration) }}
        </span>

        <!-- Volume -->
        <div class="flex items-center gap-1.5 shrink-0">
          <button @click="toggleMute" class="text-ink-tertiary hover:text-pulse transition-colors">
            <span class="material-symbols-outlined text-[18px]">
              {{ isMuted ? 'volume_off' : volume > 0.5 ? 'volume_up' : 'volume_down' }}
            </span>
          </button>
          <input type="range" min="0" max="1" step="0.01" :value="volume"
                 @input="setVolume($event.target.value)"
                 class="w-16 h-1 accent-pulse appearance-none bg-nebula-surface rounded-full cursor-pointer volume-slider" />
        </div>

        <!-- BPM Badge -->
        <div v-if="track.bpm" class="px-2 py-1 rounded-md bg-vu/10 border border-vu/20 shrink-0">
          <span class="text-[9px] text-vu font-data font-bold tabular-nums">{{ track.bpm?.toFixed(0) }} BPM</span>
        </div>

        <!-- Key Badge -->
        <div v-if="track.key && track.key !== '?'" class="px-2 py-1 rounded-md bg-laser/10 border border-laser/20 shrink-0">
          <span class="text-[9px] text-laser font-data font-bold">{{ track.key }}</span>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch, onBeforeUnmount, nextTick } from 'vue'

const props = defineProps({
  track: { type: Object, default: null },
  apiBase: { type: String, required: true }
})

const waveformContainer = ref(null)

// Player state
const isPlaying = ref(false)
const isLoading = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(0.8)
const isMuted = ref(false)

let wavesurfer = null
let currentTrackId = null

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

const initWavesurfer = async () => {
  // Dynamically import wavesurfer (client-only)
  const WaveSurfer = (await import('wavesurfer.js')).default

  if (wavesurfer) {
    wavesurfer.destroy()
    wavesurfer = null
  }

  await nextTick()

  if (!waveformContainer.value) return

  wavesurfer = WaveSurfer.create({
    container: waveformContainer.value,
    // Gradient: array of colors → vertical gradient (bottom to top)
    waveColor: ['#06b6d4', '#7c3aed', '#c026d3'],
    progressColor: ['#22d3ee', '#e0e7ff', '#e879f9'],
    cursorColor: '#f59e0b',
    cursorWidth: 2,
    barWidth: 2,
    barGap: 1,
    barRadius: 3,
    barHeight: 1.2,
    height: 48,
    normalize: true,
    fillParent: true,
    interact: true,
    dragToSeek: true,
    hideScrollbar: true,
    // WebAudio decodes the full file → pixel-accurate waveform
    backend: 'WebAudio',
  })

  wavesurfer.on('ready', (dur) => {
    duration.value = dur
    isLoading.value = false
  })

  wavesurfer.on('timeupdate', (time) => {
    currentTime.value = time
  })

  wavesurfer.on('play', () => { isPlaying.value = true })
  wavesurfer.on('pause', () => { isPlaying.value = false })
  wavesurfer.on('finish', () => { isPlaying.value = false })
  wavesurfer.on('error', (err) => {
    console.error('WaveSurfer error:', err)
    isLoading.value = false
  })

  wavesurfer.setVolume(volume.value)
}

const loadTrack = async (track) => {
  if (!track) return

  // Prevent duplicate loads
  if (currentTrackId === track.filename) return
  currentTrackId = track.filename

  isLoading.value = true
  isPlaying.value = false
  currentTime.value = 0
  duration.value = 0

  // Always destroy previous instance to avoid "operation aborted"
  if (wavesurfer) {
    try { wavesurfer.destroy() } catch (_) {}
    wavesurfer = null
  }

  await initWavesurfer()
  if (!wavesurfer) return

  const encodedFilename = encodeURIComponent(track.filename)
  const url = `${props.apiBase}/stream/${encodedFilename}`

  try {
    wavesurfer.load(url)
  } catch (e) {
    console.error('Error loading track:', e)
    isLoading.value = false
  }
}

// Controls
const togglePlay = () => {
  if (!wavesurfer) return
  wavesurfer.playPause()
}

const toggleMute = () => {
  if (!wavesurfer) return
  isMuted.value = !isMuted.value
  wavesurfer.setMuted(isMuted.value)
}

const setVolume = (val) => {
  volume.value = parseFloat(val)
  if (wavesurfer) {
    wavesurfer.setVolume(volume.value)
    if (isMuted.value && volume.value > 0) {
      isMuted.value = false
      wavesurfer.setMuted(false)
    }
  }
}

// Watch track changes
watch(() => props.track, (newTrack, oldTrack) => {
  if (newTrack) {
    loadTrack(newTrack)
  } else {
    // Track deselected — stop and destroy
    if (wavesurfer) {
      try { wavesurfer.destroy() } catch (_) {}
      wavesurfer = null
    }
    currentTrackId = null
    isPlaying.value = false
    isLoading.value = false
    currentTime.value = 0
    duration.value = 0
  }
}, { deep: true })

onBeforeUnmount(() => {
  if (wavesurfer) {
    wavesurfer.destroy()
    wavesurfer = null
  }
})
</script>

<style scoped>
/* Player slide transition */
.player-slide-enter-active { transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1); }
.player-slide-leave-active { transition: all 0.25s ease-in; }
.player-slide-enter-from { transform: translateY(100%); opacity: 0; }
.player-slide-leave-to { transform: translateY(100%); opacity: 0; }

/* Volume slider styling */
.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #06b6d4;
  cursor: pointer;
  border: none;
}
.volume-slider::-webkit-slider-runnable-track {
  height: 3px;
  background: rgba(255,255,255,0.08);
  border-radius: 4px;
}
</style>
