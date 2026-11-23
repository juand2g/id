<template>
  <div class="w-full h-full relative">
    <TresCanvas :clear-color="'#00000000'" :alpha="true" window-size>
      <TresPerspectiveCamera ref="cameraRef" :position="[50, 35, 50]" :look-at="[0, 0, 0]" />
      <OrbitControls ref="controlsRef" :enable-damping="true" :damping-factor="0.05" :auto-rotate="!selectedTrack" :auto-rotate-speed="0.3" />

      <!-- Lighting -->
      <TresAmbientLight :intensity="0.15" />
      <TresPointLight :position="[60, 45, 40]" :intensity="6" color="#06b6d4" :distance="250" />
      <TresPointLight :position="[-50, -25, -40]" :intensity="5" color="#c026d3" :distance="220" />
      <TresPointLight :position="[0, 60, 0]" :intensity="2.5" color="#7c3aed" :distance="180" />

      <!-- Starfield -->
      <Stars :radius="200" :count="1500" :size="0.4" :depth="150" />

      <!-- INSTANCED NODES (single draw call for ALL tracks) -->
      <primitive :key="instancedMesh.uuid" :object="instancedMesh" @click="onInstanceClick" />

      <!-- Selected node glow ring -->
      <TresGroup v-if="selectedTrack && selectedPos" :position="selectedPos">
        <TresMesh :rotation="[Math.PI/2, 0, 0]" :scale="ringScale">
          <TresRingGeometry :args="[0.6, 0.75, 64]" />
          <TresMeshBasicMaterial color="#e879f9" :transparent="true" :opacity="0.5" :side="2" :blending="2" />
        </TresMesh>
        <TresMesh :rotation="[0, 0, Math.PI/2]" :scale="ringScale">
          <TresRingGeometry :args="[0.8, 0.9, 64]" />
          <TresMeshBasicMaterial color="#06b6d4" :transparent="true" :opacity="0.3" :side="2" :blending="2" />
        </TresMesh>
      </TresGroup>

      <!-- Grid + Fog -->
      <TresGridHelper :args="[500, 80, '#0a0a14', '#080810']" :position="[0, -25, 0]" />
      <TresFog :color="'#050508'" :near="80" :far="450" />

      <!-- Post-processing Bloom -->
      <Suspense>
        <EffectComposerPmndrs>
          <BloomPmndrs
            :intensity="1.5"
            :luminance-threshold="0.15"
            :luminance-smoothing="0.8"
            :radius="0.85"
          />
        </EffectComposerPmndrs>
      </Suspense>
    </TresCanvas>
  </div>
</template>

<script setup>
import { OrbitControls, Stars } from '@tresjs/cientos'
import { EffectComposerPmndrs, BloomPmndrs } from '@tresjs/post-processing'
import { ref, watch, onMounted, onBeforeUnmount, shallowRef, computed } from 'vue'
import * as THREE from 'three'

const props = defineProps({
  tracks: { type: Array, default: () => [] },
  selectedTrack: { type: Object, default: null }
})

const emit = defineEmits(['select'])

// ========== REFS ==========
const cameraRef = ref(null)
const controlsRef = ref(null)

// ========== INSTANCED MESH ==========
const geometry = new THREE.SphereGeometry(0.25, 12, 12)
const material = new THREE.MeshStandardMaterial({
  color: 0xffffff,
  emissive: 0xffffff,
  roughness: 0.2,
  metalness: 0.6,
  transparent: true,
  opacity: 0.95,
  emissiveIntensity: 2.0,
})

const instancedMesh = shallowRef(new THREE.InstancedMesh(geometry, material, 1))
instancedMesh.value.instanceMatrix.setUsage(THREE.DynamicDrawUsage)

let trackIndexMap = []
let selectedInstanceIdx = -1

const dummy = new THREE.Object3D()

const colorPalette = [
  new THREE.Color('#38bdf8'),
  new THREE.Color('#06b6d4'),
  new THREE.Color('#7c3aed'),
  new THREE.Color('#c026d3'),
  new THREE.Color('#f0abfc'),
]

const fuchsiaColor = new THREE.Color('#e879f9')
const fuchsiaBright = new THREE.Color('#ff6fff')

const getColor = (energy, isSelected) => {
  if (isSelected) return fuchsiaColor.clone()
  if (energy > 0.75) return colorPalette[4]
  if (energy > 0.6) return colorPalette[3]
  if (energy > 0.45) return colorPalette[2]
  if (energy > 0.3) return colorPalette[1]
  return colorPalette[0]
}

// Stable position hashing
const hashString = (str) => {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = Math.imul(31, hash) + str.charCodeAt(i) | 0
  }
  return hash >>> 0
}

const mulberry32 = (seed) => {
  return () => {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0
    let t = Math.imul(seed ^ seed >>> 15, 1 | seed)
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t
    return ((t ^ t >>> 14) >>> 0) / 4294967296
  }
}

const posCache = new Map()
const getPosition = (track) => {
  if (track.umap_coords?.x != null) {
    return [track.umap_coords.x * 15, track.umap_coords.y * 15, track.umap_coords.z * 15]
  }
  if (posCache.has(track.filename)) return posCache.get(track.filename)
  const rng = mulberry32(hashString(track.filename))
  const pos = [(rng() - 0.5) * 80, (rng() - 0.5) * 80, (rng() - 0.5) * 80]
  posCache.set(track.filename, pos)
  return pos
}

// ========== UPDATE INSTANCES ==========
const updateInstances = () => {
  const tracks = props.tracks
  const count = tracks.length

  if (count === 0) {
    instancedMesh.value.visible = false
    trackIndexMap = []
    selectedInstanceIdx = -1
    return
  }

  if (instancedMesh.value.count !== count) {
    const oldMesh = instancedMesh.value
    const newMesh = new THREE.InstancedMesh(geometry, material, count)
    newMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage)
    newMesh.visible = true
    instancedMesh.value = newMesh
    oldMesh.dispose()
  } else {
    instancedMesh.value.visible = true
  }

  trackIndexMap = []
  selectedInstanceIdx = -1

  for (let i = 0; i < count; i++) {
    const track = tracks[i]
    const pos = getPosition(track)
    const isSelected = props.selectedTrack?.filename === track.filename

    if (isSelected) selectedInstanceIdx = i

    const dur = track.duration || 180
    const t = Math.min(Math.max((dur - 60) / 540, 0), 1)
    const baseScale = 0.7 + t * 1.4
    const scale = isSelected ? baseScale * 1.8 : baseScale

    dummy.position.set(pos[0], pos[1], pos[2])
    dummy.scale.set(scale, scale, scale)
    dummy.updateMatrix()

    instancedMesh.value.setMatrixAt(i, dummy.matrix)
    instancedMesh.value.setColorAt(i, getColor(track.energy || 0, isSelected))

    trackIndexMap.push(track)
  }

  instancedMesh.value.instanceMatrix.needsUpdate = true
  if (instancedMesh.value.instanceColor) instancedMesh.value.instanceColor.needsUpdate = true
}

watch(() => [props.tracks, props.selectedTrack], updateInstances, { deep: false, immediate: true })

// ========== CAMERA AUTO-CENTER ON SELECTION ==========
let cameraAnimId = null
const cameraTarget = new THREE.Vector3()
const cameraLerp = new THREE.Vector3()

const flyToNode = (pos) => {
  if (cameraAnimId) cancelAnimationFrame(cameraAnimId)

  const targetPos = new THREE.Vector3(pos[0], pos[1], pos[2])
  const offset = new THREE.Vector3(8, 5, 8) // Camera offset from node
  const cameraDestination = targetPos.clone().add(offset)

  let progress = 0

  const animateCamera = () => {
    progress += 0.02
    const t = Math.min(progress, 1)
    // Smooth ease-out
    const ease = 1 - Math.pow(1 - t, 3)

    // Get controls instance
    const controls = controlsRef.value?.value || controlsRef.value?.instance
    const camera = cameraRef.value?.value || cameraRef.value?.instance

    if (controls && controls.target) {
      controls.target.lerp(targetPos, ease * 0.08)
    }

    if (camera) {
      camera.position.lerp(cameraDestination, ease * 0.06)
    }

    if (t < 1) {
      cameraAnimId = requestAnimationFrame(animateCamera)
    } else {
      cameraAnimId = null
    }
  }

  cameraAnimId = requestAnimationFrame(animateCamera)
}

// When selectedTrack changes, fly camera to it
watch(() => props.selectedTrack, (track) => {
  if (track) {
    const pos = getPosition(track)
    flyToNode(pos)
  }
})

// ========== CLICK HANDLER ==========
const onInstanceClick = (event) => {
  if (event.instanceId !== undefined && trackIndexMap[event.instanceId]) {
    emit('select', trackIndexMap[event.instanceId])
  }
}

// ========== SELECTED NODE POSITION ==========
const selectedPos = computed(() => {
  if (!props.selectedTrack) return null
  return getPosition(props.selectedTrack)
})

// ========== ANIMATION: Ring pulse + Fuchsia breathing ==========
const ringScale = ref([1, 1, 1])
let animFrame = null
let startTime = 0

const tempColor = new THREE.Color()

const animate = () => {
  const elapsed = (performance.now() - startTime) / 1000
  const pulse = 1 + Math.sin(elapsed * 3) * 0.12
  ringScale.value = [pulse, pulse, pulse]

  // Breathing fuchsia for selected node
  if (selectedInstanceIdx >= 0 && instancedMesh.value?.instanceColor) {
    const breathe = 0.6 + Math.sin(elapsed * 2.5) * 0.4 // 0.2 to 1.0
    tempColor.lerpColors(fuchsiaColor, fuchsiaBright, breathe)
    instancedMesh.value.setColorAt(selectedInstanceIdx, tempColor)
    instancedMesh.value.instanceColor.needsUpdate = true
  }

  animFrame = requestAnimationFrame(animate)
}

onMounted(() => {
  startTime = performance.now()
  animFrame = requestAnimationFrame(animate)
})

onBeforeUnmount(() => {
  if (animFrame) cancelAnimationFrame(animFrame)
  if (cameraAnimId) cancelAnimationFrame(cameraAnimId)
  instancedMesh.value?.dispose()
})
</script>