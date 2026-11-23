<template>
  <div class="h-screen w-full overflow-hidden flex font-display bg-nebula-void text-ink-primary selection:bg-pulse selection:text-black" :class="selectedTrack && currentView !== 'mix' ? 'pb-[60px]' : ''">

    <!-- SIDEBAR: Frequency Scanner -->
    <aside class="w-[320px] shrink-0 flex flex-col border-r border-white/[0.06] bg-nebula-deep h-full relative z-20">

      <!-- Logo + Status -->
      <div class="px-5 pt-5 pb-4 border-b border-white/[0.06]">
        <div class="flex items-center justify-between mb-4">
          <h1 class="text-lg font-bold tracking-tight">
            <span class="text-ink-primary">ID</span><span class="text-ink-tertiary">_</span><span class="bg-gradient-to-r from-pulse to-laser bg-clip-text text-transparent">SYSTEM</span>
          </h1>
          <div class="flex items-center gap-1.5 px-2 py-1 rounded-md bg-nebula-surface border border-white/[0.06]">
            <div :class="status === 'CONNECTED' ? 'bg-pulse' : 'bg-red-500'" class="size-1.5 rounded-full animate-pulse-glow"></div>
            <span class="text-[10px] font-data font-medium text-ink-tertiary tracking-wider">{{ status }}</span>
          </div>
        </div>

        <!-- View Switcher -->
        <!-- Single view: NEBULA (Sonic Galaxy) -->
        <div class="flex gap-1 p-1 bg-nebula-void rounded-lg border border-white/[0.04]">
          <div
            class="flex-1 py-2 text-[10px] font-semibold tracking-[0.15em] rounded-md transition-all border bg-gradient-to-r from-pulse/20 to-pulse/10 text-pulse shadow-[inset_0_0_12px_rgba(6,182,212,0.15)] border-pulse/30 text-center">
            NEBULA
          </div>
        </div>
      </div>

      <!-- Search (sidebar) -->
      <div class="px-4 py-3 border-b border-white/[0.06]">
        <div class="relative mb-2">
          <span class="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-muted text-[16px]">search</span>
          <input v-model="searchQuery" placeholder="Search tracks..."
                 class="w-full bg-nebula-void/60 border border-white/[0.06] rounded-md pl-8 pr-3 py-1.5 text-[11px] text-ink-primary placeholder-ink-muted focus:outline-none focus:border-pulse/40 transition-colors font-data" />
        </div>
        <!-- Key filter + Harmonic toggle -->
        <div class="flex items-center gap-1.5">
          <select v-model="keyFilter"
                  class="flex-1 bg-nebula-void/60 border border-white/[0.06] rounded-md px-2 py-1 text-[10px] text-ink-secondary font-data focus:outline-none focus:border-pulse/40 transition-colors appearance-none">
            <option value="">All Keys</option>
            <option v-for="k in availableKeys" :key="k" :value="k">{{ k }} · {{ keyToCamelot(k) || '?' }}</option>
          </select>
          <button @click="harmonicFilter = !harmonicFilter"
                  class="px-2 py-1 rounded-md text-[8px] font-data font-bold tracking-wider border transition-all whitespace-nowrap"
                  :class="harmonicFilter
                    ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.2)]'
                    : 'bg-white/[0.02] border-white/[0.06] text-white/20 hover:text-white/40'">
            ♪ HARMONIC
          </button>
        </div>
      </div>

      <!-- Track List -->
      <div class="flex-1 overflow-y-auto custom-scrollbar flex flex-col">
        <div v-for="track in filteredTracks" :key="track.filename"
             @click="selectTrack(track)"
             :class="getTrackHighlight(track)"
             class="relative px-4 py-3 border-b border-white/[0.04] border-l-2 transition-all group cursor-pointer">

          <!-- Track Info -->
          <div class="flex flex-col gap-1 relative z-10">
            <div class="flex justify-between items-center">
              <p :class="selectedTrack?.filename === track.filename ? 'text-ink-primary' : 'text-ink-secondary'"
                 class="text-[11px] font-medium truncate tracking-wide group-hover:text-ink-primary transition-colors pr-2 max-w-[180px]">
                {{ track.title || track.filename }}
              </p>
              <div class="flex items-center gap-1.5 shrink-0">
                <span v-if="keyToCamelot(track.key)" class="text-[7px] font-data font-bold px-1 py-0.5 rounded border"
                      :style="{ color: camelotColor(keyToCamelot(track.key)), borderColor: camelotColor(keyToCamelot(track.key)) + '40', backgroundColor: camelotColor(keyToCamelot(track.key)) + '15' }">
                  {{ keyToCamelot(track.key) }}
                </span>
                <span v-if="track.bpm" class="text-[9px] font-data font-bold text-vu tabular-nums">{{ track.bpm?.toFixed(0) }}</span>
              </div>
            </div>
            <p class="text-ink-muted text-[10px] truncate max-w-[180px]">{{ track.artist || 'Unknown' }}</p>
          </div>

          <!-- Energy Bar -->
          <div class="absolute bottom-0 left-0 h-[2px] transition-all duration-500"
               :style="{ width: ((track.energy || 0) * 100) + '%' }"
               :class="getEnergyBarColor(track)">
          </div>
        </div>
      </div>

      <!-- Bottom Stats -->
      <div class="px-4 py-3 border-t border-white/[0.06] bg-nebula-void/80">
        <div class="flex items-center justify-between">
          <span class="text-[10px] text-ink-muted font-data">
            <span class="text-pulse">{{ filteredTracks.length }}</span> / {{ tracks.length }} signals
          </span>
          <span class="text-[10px] text-ink-muted font-data">v2.0</span>
        </div>
      </div>
    </aside>

    <!-- MAIN VIEWPORT -->
    <main class="flex-1 relative bg-nebula-void flex flex-col overflow-hidden">

      <!-- Nebula Background: Multi-color breathing blobs -->
      <div class="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        <!-- Cyan blob — top left -->
        <div class="absolute -top-[20%] -left-[10%] w-[60%] h-[60%] rounded-full blur-[120px] opacity-[0.15] animate-nebula-1 bg-[#06b6d4]"></div>
        <!-- Magenta blob — bottom right -->
        <div class="absolute -bottom-[15%] -right-[5%] w-[50%] h-[50%] rounded-full blur-[100px] opacity-[0.12] animate-nebula-2 bg-[#c026d3]"></div>
        <!-- Violet blob — center -->
        <div class="absolute top-[30%] left-[40%] w-[40%] h-[40%] rounded-full blur-[130px] opacity-[0.1] animate-nebula-3 bg-[#7c3aed]"></div>
        <!-- Amber blob — top right (subtle) -->
        <div class="absolute -top-[10%] right-[20%] w-[35%] h-[35%] rounded-full blur-[110px] opacity-[0.08] animate-nebula-4 bg-[#f59e0b]"></div>
      </div>

      <!-- TOP BAR (Overlay) — hidden in mix mode -->
      <header v-if="currentView === 'galaxy'" class="absolute top-0 left-0 w-full z-40 p-5 pointer-events-none">
        <!-- Row 1: Stats + Scan + Mode -->
        <div class="flex justify-between items-start mb-3">
          <div class="pointer-events-auto flex gap-3">
            <!-- Signal Count -->
            <div class="bg-nebula-deep/80 backdrop-blur-xl border border-white/[0.06] rounded-lg px-4 py-3 min-w-[120px]">
              <span class="text-[9px] text-pulse font-data tracking-[0.2em] uppercase block mb-1">Signals</span>
              <div class="text-2xl font-bold text-ink-primary leading-none font-data tabular-nums">{{ filteredTracks.length }}</div>
            </div>

          <!-- Scan Button -->
          <button @click="scanLibrary" :disabled="isScanning"
              class="bg-nebula-deep/80 backdrop-blur-xl border border-white/[0.06] hover:border-pulse/40 rounded-lg px-4 py-3 flex items-center gap-3 group transition-all disabled:opacity-40">
            <div class="size-8 rounded-md flex items-center justify-center bg-pulse/10 group-hover:bg-pulse/20 transition-colors">
              <svg v-if="isScanning" class="animate-spin size-4 text-pulse" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span v-else class="material-symbols-outlined text-pulse text-[18px]">radar</span>
            </div>
            <div class="text-left">
              <span class="block text-[9px] text-ink-tertiary tracking-[0.15em] font-semibold">
                {{ isScanning ? 'SCANNING...' : 'SYSTEM SCAN' }}
              </span>
              <span class="block text-[9px] text-ink-muted font-data">
                {{ isScanning ? 'Indexing...' : 'Update Library' }}
              </span>
            </div>
          </button>
          </div>

          <!-- Right: Mode Indicator -->
          <div class="pointer-events-auto bg-nebula-deep/80 backdrop-blur-xl border border-white/[0.06] px-3 py-1.5 rounded-md flex items-center gap-2">
            <div class="size-1.5 bg-pulse rounded-full animate-breathe"></div>
            <span class="text-[10px] font-data font-medium text-pulse/80 tracking-[0.15em]">LIVE RENDER</span>
          </div>
        </div>

        <!-- Row 2: Filter Controls -->
        <div class="pointer-events-auto flex items-center gap-3 flex-wrap">
          <!-- BPM Range -->
          <div class="bg-nebula-deep/80 backdrop-blur-xl border border-white/[0.06] rounded-lg px-4 py-2.5 flex items-center gap-3">
            <span class="text-[9px] font-data text-ink-tertiary tracking-[0.15em] shrink-0">BPM</span>
            <input type="range" :min="0" :max="200" v-model.number="bpmRange[0]" class="w-[80px] filter-slider" />
            <span class="text-[9px] font-data text-vu tabular-nums shrink-0">{{ bpmRange[0] }} — {{ bpmRange[1] }}</span>
            <input type="range" :min="100" :max="300" v-model.number="bpmRange[1]" class="w-[80px] filter-slider" />
          </div>

          <!-- Energy Chips -->
          <div class="bg-nebula-deep/80 backdrop-blur-xl border border-white/[0.06] rounded-lg px-3 py-2 flex items-center gap-1.5">
            <span class="text-[9px] font-data text-ink-tertiary tracking-[0.15em] mr-1">ENERGY</span>
            <button v-for="level in ['ALL', 'LOW', 'MID', 'HIGH']" :key="level"
                    @click="energyFilter = level"
                    :class="energyFilter === level
                      ? level === 'HIGH' ? 'bg-laser/20 text-laser border-laser/30'
                      : level === 'MID' ? 'bg-pulse/20 text-pulse border-pulse/30'
                      : level === 'LOW' ? 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30'
                      : 'bg-white/10 text-ink-primary border-white/20'
                      : 'text-ink-muted hover:text-ink-secondary border-transparent'"
                    class="px-2 py-0.5 rounded text-[9px] font-data font-bold tracking-wider border transition-all">
              {{ level }}
            </button>
          </div>

          <!-- Reset -->
          <button v-if="hasActiveFilters" @click="resetFilters"
                  class="bg-nebula-deep/80 backdrop-blur-xl border border-red-500/20 rounded-lg px-3 py-2 text-[9px] font-data text-red-400 hover:border-red-500/40 hover:text-red-300 transition-all">
            ✕ RESET
          </button>
        </div>
      </header>

      <!-- 3D Viewport -->
      <div v-if="currentView === 'galaxy'" class="w-full h-full relative z-10">
        <ClientOnly>
          <SonicGalaxy :tracks="filteredTracks" :selectedTrack="selectedTrack" @select="selectTrack" />
        </ClientOnly>

        <!-- Track Detail Panel (Right Overlay) -->
        <transition name="slide-fade">
          <div v-if="selectedTrack" class="absolute top-0 right-0 h-full w-[380px] z-30 pointer-events-none flex flex-col justify-center pr-5">
            <div class="bg-nebula-deep/95 backdrop-blur-2xl border border-pulse/20 p-7 rounded-xl pointer-events-auto relative overflow-hidden animate-fade-in shadow-[0_0_40px_rgba(6,182,212,0.08)]">

              <!-- Decorative glow -->
              <div class="absolute -bottom-16 -left-16 w-48 h-48 rounded-full blur-[80px] pointer-events-none"
                   :class="selectedTrack.energy > 0.6 ? 'bg-laser/20' : 'bg-pulse/15'"></div>

              <!-- Close button -->
              <button @click="selectedTrack = null" class="absolute top-4 right-4 text-ink-muted hover:text-ink-primary transition-colors">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>

              <!-- Header -->
              <div class="mb-6 relative z-10">
                <span class="text-[9px] text-pulse font-data font-bold tracking-[0.2em] uppercase mb-2 block">Signal Analysis</span>
                <h1 class="text-2xl font-bold text-ink-primary leading-tight mb-1.5 break-words">{{ selectedTrack.title || selectedTrack.filename }}</h1>
                <h2 class="text-sm text-ink-tertiary">{{ selectedTrack.artist }}</h2>
              </div>

              <!-- Metrics Grid -->
              <div class="grid grid-cols-2 gap-3 mb-6 relative z-10">
                <!-- BPM -->
                <div class="bg-nebula-surface/60 p-4 rounded-lg border border-white/[0.04] hover:border-vu/30 transition-all group/m">
                  <span class="text-[8px] text-ink-muted uppercase tracking-[0.2em] block mb-1.5 font-data">Tempo</span>
                  <div class="flex items-baseline gap-1">
                    <span class="text-3xl font-bold text-vu group-hover/m:text-vu-glow transition-colors font-data tabular-nums">{{ selectedTrack.bpm?.toFixed(0) || '---' }}</span>
                    <span class="text-[10px] text-ink-muted font-data">BPM</span>
                  </div>
                </div>

                <!-- Key -->
                <div class="bg-nebula-surface/60 p-4 rounded-lg border border-white/[0.04] hover:border-laser/30 transition-all group/m">
                  <span class="text-[8px] text-ink-muted uppercase tracking-[0.2em] block mb-1.5 font-data">Key</span>
                  <div class="flex items-baseline gap-1">
                    <span class="text-3xl font-bold text-laser group-hover/m:text-laser-glow transition-colors font-data">{{ selectedTrack.key || '?' }}</span>
                  </div>
                </div>
              </div>

              <!-- Energy Meter -->
              <div class="mb-6 relative z-10">
                <div class="flex justify-between items-end mb-2">
                  <span class="text-[9px] text-ink-muted uppercase tracking-[0.15em] font-data">Energy</span>
                  <span class="text-sm font-bold text-ink-secondary font-data tabular-nums">{{ (selectedTrack.energy * 100).toFixed(0) }}<span class="text-ink-muted text-[10px]">%</span></span>
                </div>
                <div class="h-1.5 bg-nebula-surface rounded-full overflow-hidden">
                  <div class="h-full rounded-full relative transition-all duration-700"
                       :class="selectedTrack.energy > 0.7 ? 'bg-gradient-to-r from-vu via-laser to-laser-glow' : 'bg-gradient-to-r from-pulse to-pulse-glow'"
                       :style="{ width: (selectedTrack.energy * 100) + '%' }">
                    <div class="absolute top-0 right-0 h-full w-3 bg-white/40 blur-[3px]"></div>
                  </div>
                </div>
              </div>

              <!-- Footer Tags -->
              <div class="flex gap-2 flex-wrap relative z-10">
                <div class="px-2.5 py-1 rounded-md bg-nebula-surface border border-white/[0.04] text-[10px] text-ink-tertiary font-data">
                  {{ (selectedTrack.duration / 60).toFixed(1) }} min
                </div>
                <div v-if="selectedTrack.genre" class="px-2.5 py-1 rounded-md bg-nebula-surface border border-white/[0.04] text-[10px] text-ink-tertiary font-data uppercase">
                  {{ selectedTrack.genre }}
                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>

    </main>

    <!-- Waveform Player (Bottom Bar) -->
    <ClientOnly>
      <WaveformPlayer :track="selectedTrack" :apiBase="apiBase" />
    </ClientOnly>
  </div>
</template>

<script setup>
import SonicGalaxy from '../components/SonicGalaxy.vue'
import WaveformPlayer from '../components/WaveformPlayer.vue'
import { keyToCamelot, camelotColor, isCompatible } from '../composables/useCamelot.js'

const config = useRuntimeConfig()
const apiBase = config.public.apiBase

// UI State
const status = ref('CONNECTED')
const isScanning = ref(false)

// Data State
const tracks = ref([])
const selectedTrack = ref(null)

// Highlight logic for track list
const getTrackHighlight = (track) => {
  // Harmonic compatibility highlight when a track is selected
  if (selectedTrack.value && selectedTrack.value.filename !== track.filename) {
    const selectedCamelot = keyToCamelot(selectedTrack.value.key)
    const trackCamelot = keyToCamelot(track.key)
    if (selectedCamelot && trackCamelot && isCompatible(trackCamelot, selectedCamelot)) {
      return 'bg-emerald-500/[0.06] border-l-emerald-500/60 hover:bg-emerald-500/[0.1]'
    }
  }
  return selectedTrack.value?.filename === track.filename
    ? 'bg-pulse/[0.08] border-l-pulse'
    : 'border-l-transparent hover:bg-white/[0.02] hover:border-l-pulse/40'
}

// ========== FILTERS ==========
const searchQuery = ref('')
const bpmRange = ref([0, 300])
const energyFilter = ref('ALL')
const keyFilter = ref('')
const harmonicFilter = ref(false)

// Available keys from loaded tracks
const availableKeys = computed(() => {
  const keys = new Set()
  tracks.value.forEach(t => {
    if (t.key && t.key !== '?' && t.key !== 'Unknown') keys.add(t.key)
  })
  return Array.from(keys).sort()
})

const hasActiveFilters = computed(() => {
  return searchQuery.value !== '' || bpmRange.value[0] > 0 || bpmRange.value[1] < 300 || energyFilter.value !== 'ALL' || keyFilter.value !== '' || harmonicFilter.value
})

const resetFilters = () => {
  searchQuery.value = ''
  bpmRange.value = [0, 300]
  energyFilter.value = 'ALL'
  keyFilter.value = ''
  harmonicFilter.value = false
}

const filteredTracks = computed(() => {
  let result = tracks.value

  // Search filter (name or artist)
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase().trim()
    result = result.filter(t =>
      (t.title || t.filename || '').toLowerCase().includes(q) ||
      (t.artist || '').toLowerCase().includes(q)
    )
  }

  // BPM range filter
  const [minBpm, maxBpm] = bpmRange.value
  if (minBpm > 0 || maxBpm < 300) {
    result = result.filter(t => {
      const bpm = t.bpm || 0
      if (bpm === 0) return true // Show tracks without BPM data
      return bpm >= minBpm && bpm <= maxBpm
    })
  }

  // Energy filter
  if (energyFilter.value !== 'ALL') {
    result = result.filter(t => {
      const e = t.energy || 0
      if (e === 0) return energyFilter.value !== 'HIGH'
      if (energyFilter.value === 'LOW') return e <= 0.35
      if (energyFilter.value === 'MID') return e > 0.35 && e <= 0.7
      if (energyFilter.value === 'HIGH') return e > 0.7
      return true
    })
  }

  // Key filter
  if (keyFilter.value) {
    result = result.filter(t => t.key === keyFilter.value)
  }

  // Harmonic filter — show tracks compatible with selected track
  if (harmonicFilter.value && selectedTrack.value) {
    const selectedCamelot = keyToCamelot(selectedTrack.value.key)
    if (selectedCamelot) {
      result = result.filter(t => {
        const tc = keyToCamelot(t.key)
        if (!tc) return false
        return isCompatible(tc, selectedCamelot) || t.filename === selectedTrack.value.filename
      })
    }
  }

  return result
})

// Visual: Breathing gradient based on selected track energy
const breathingGradientStyle = computed(() => {
  if (!selectedTrack.value) {
    return { background: 'radial-gradient(ellipse at 60% 50%, rgba(6,182,212,0.08) 0%, rgba(124,58,237,0.04) 40%, transparent 70%)' }
  }
  const energy = selectedTrack.value.energy || 0
  if (energy > 0.7) {
    return { background: 'radial-gradient(ellipse at 60% 50%, rgba(192,38,211,0.18) 0%, rgba(245,158,11,0.06) 35%, transparent 65%)' }
  }
  return { background: 'radial-gradient(ellipse at 60% 50%, rgba(6,182,212,0.14) 0%, rgba(124,58,237,0.06) 35%, transparent 65%)' }
})

// Energy bar color helper
const getEnergyBarColor = (track) => {
  const e = track.energy || 0
  if (e > 0.7) return 'bg-gradient-to-r from-laser to-laser-glow'
  if (e > 0.4) return 'bg-gradient-to-r from-pulse to-pulse-glow'
  return 'bg-gradient-to-r from-ink-muted to-ink-tertiary'
}

// 1. Cargar Tracks
const fetchTracks = async () => {
  try {
    const res = await fetch(`${apiBase}/tracks?limit=10000`)
    const data = await res.json()
    const rawTracks = Array.isArray(data) ? data : (data.items || [])

    const uniqueMap = new Map()
    rawTracks.forEach(t => {
        if (!uniqueMap.has(t.filename)) {
            uniqueMap.set(t.filename, t)
        }
    })

    tracks.value = Array.from(uniqueMap.values()).map(t => ({
        ...t,
        ...t.analysis,
        title: t.analysis?.title || t.filename,
        artist: t.analysis?.artist || 'Unknown Artist',
        key: t.analysis?.key || '?',
        bpm: t.analysis?.bpm || 0,
        energy: t.analysis?.energy || 0
    }))

    console.log("Tracks loaded:", tracks.value.length)
    // Debug: energy distribution
    const energyDist = { noData: 0, low: 0, mid: 0, high: 0 }
    tracks.value.forEach(t => {
      const e = t.energy || 0
      if (e === 0) energyDist.noData++
      else if (e <= 0.35) energyDist.low++
      else if (e <= 0.7) energyDist.mid++
      else energyDist.high++
    })
    console.log("Energy distribution:", energyDist)
    status.value = 'CONNECTED'
  } catch (e) {
    status.value = 'OFFLINE'
    console.error(e)
  }
}

// 2. Scan Logic
const scanLibrary = async () => {
  if (isScanning.value) return
  isScanning.value = true

  try {
    await fetch(`${apiBase}/scan`, { method: 'POST' })

    let stableCount = 0
    const pollInterval = setInterval(async () => {
        const previousCount = tracks.value.length
        await fetchTracks()

        if (tracks.value.length === previousCount) {
            stableCount++
        } else {
            stableCount = 0
        }

        if (stableCount >= 5) {
            clearInterval(pollInterval)
            isScanning.value = false
            await fetch(`${apiBase}/map/generate`, { method: 'POST' })
            setTimeout(async () => {
                await fetchTracks()
            }, 5000)
        }
    }, 3000)

  } catch (e) {
    console.error(e)
    isScanning.value = false
  }
}

const selectTrack = (track) => {
    selectedTrack.value = track
}

// ========== KEYBOARD NAVIGATION ==========
const navigateTrack = (direction) => {
  const list = filteredTracks.value
  if (!list.length) return
  const currentIdx = list.findIndex(t => t.filename === selectedTrack.value?.filename)
  let nextIdx = direction === 'next' ? currentIdx + 1 : currentIdx - 1
  if (nextIdx < 0) nextIdx = list.length - 1
  if (nextIdx >= list.length) nextIdx = 0
  selectTrack(list[nextIdx])
}

const handleKeydown = (e) => {
  // Don't capture when typing in search input
  if (e.target.tagName === 'INPUT') return

  if (e.code === 'ArrowDown' || e.code === 'KeyJ') {
    e.preventDefault()
    navigateTrack('next')
  } else if (e.code === 'ArrowUp' || e.code === 'KeyK') {
    e.preventDefault()
    navigateTrack('prev')
  }
}

onMounted(() => {
  fetchTracks()
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style>
/* Transitions */
.slide-fade-enter-active { transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1); }
.slide-fade-leave-active { transition: all 0.25s ease-in; }
.slide-fade-enter-from { opacity: 0; transform: translateX(24px); }
.slide-fade-leave-to { opacity: 0; transform: translateX(24px); }

/* Custom Scrollbar */
.custom-scrollbar::-webkit-scrollbar { width: 3px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(6, 182, 212, 0.3); }

/* Filter Sliders */
.filter-slider { -webkit-appearance: none; appearance: none; background: rgba(255,255,255,0.06); border-radius: 999px; height: 4px; }
.filter-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px; height: 12px;
  border-radius: 50%;
  background: #06b6d4;
  cursor: pointer;
  border: 2px solid rgba(6, 182, 212, 0.4);
  box-shadow: 0 0 8px rgba(6, 182, 212, 0.3);
  transition: box-shadow 0.2s;
}
.filter-slider::-webkit-slider-thumb:hover {
  box-shadow: 0 0 16px rgba(6, 182, 212, 0.5);
}
.filter-slider::-moz-range-thumb {
  width: 12px; height: 12px;
  border-radius: 50%;
  background: #06b6d4;
  cursor: pointer;
  border: 2px solid rgba(6, 182, 212, 0.4);
  box-shadow: 0 0 8px rgba(6, 182, 212, 0.3);
}
</style>