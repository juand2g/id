/**
 * Camelot Wheel — Harmonic Mixing System
 *
 * Maps musical keys to Camelot codes and provides compatibility checks.
 * Compatible keys: same code, ±1 on wheel, inner/outer switch (A↔B).
 *
 * Supports formats: standard (Am, C), ID3 (Amin, Cmaj), descriptive (A minor, C major),
 * OpenKey (1m, 1d), Camelot native (8A, 8B), Rekordbox numeric, and librosa output.
 */

// Musical key → Camelot code (exhaustive mapping)
const KEY_TO_CAMELOT = {
    // ── Major keys (B = major) ──
    'C': '8B', 'Cmaj': '8B', 'C major': '8B', 'C Major': '8B',
    'Db': '3B', 'C#': '3B', 'C#maj': '3B', 'Db major': '3B', 'Db Major': '3B', 'C# major': '3B', 'C# Major': '3B',
    'D': '10B', 'Dmaj': '10B', 'D major': '10B', 'D Major': '10B',
    'Eb': '5B', 'D#': '5B', 'Ebmaj': '5B', 'Eb major': '5B', 'Eb Major': '5B', 'D# major': '5B', 'D# Major': '5B',
    'E': '12B', 'Emaj': '12B', 'E major': '12B', 'E Major': '12B',
    'F': '7B', 'Fmaj': '7B', 'F major': '7B', 'F Major': '7B',
    'F#': '2B', 'Gb': '2B', 'F#maj': '2B', 'Gb major': '2B', 'Gb Major': '2B', 'F# major': '2B', 'F# Major': '2B',
    'G': '9B', 'Gmaj': '9B', 'G major': '9B', 'G Major': '9B',
    'Ab': '4B', 'G#': '4B', 'Abmaj': '4B', 'Ab major': '4B', 'Ab Major': '4B', 'G# major': '4B', 'G# Major': '4B',
    'A': '11B', 'Amaj': '11B', 'A major': '11B', 'A Major': '11B',
    'Bb': '6B', 'A#': '6B', 'Bbmaj': '6B', 'Bb major': '6B', 'Bb Major': '6B', 'A# major': '6B', 'A# Major': '6B',
    'B': '1B', 'Bmaj': '1B', 'B major': '1B', 'B Major': '1B',

    // ── Minor keys (A = minor) ──
    'Am': '8A', 'Amin': '8A', 'A minor': '8A', 'A Minor': '8A',
    'Bbm': '3A', 'A#m': '3A', 'Bbmin': '3A', 'Bb minor': '3A', 'Bb Minor': '3A', 'A#min': '3A', 'A# minor': '3A',
    'Bm': '10A', 'Bmin': '10A', 'B minor': '10A', 'B Minor': '10A',
    'Cm': '5A', 'Cmin': '5A', 'C minor': '5A', 'C Minor': '5A',
    'C#m': '12A', 'Dbm': '12A', 'C#min': '12A', 'Db minor': '12A', 'Db Minor': '12A', 'C# minor': '12A', 'Dbmin': '12A',
    'Dm': '7A', 'Dmin': '7A', 'D minor': '7A', 'D Minor': '7A',
    'D#m': '2A', 'Ebm': '2A', 'D#min': '2A', 'Eb minor': '2A', 'Eb Minor': '2A', 'Ebmin': '2A', 'D# minor': '2A',
    'Em': '9A', 'Emin': '9A', 'E minor': '9A', 'E Minor': '9A',
    'Fm': '4A', 'Fmin': '4A', 'F minor': '4A', 'F Minor': '4A',
    'F#m': '11A', 'F#min': '11A', 'F# minor': '11A', 'F# Minor': '11A', 'Gbm': '11A', 'Gbmin': '11A',
    'Gm': '6A', 'Gmin': '6A', 'G minor': '6A', 'G Minor': '6A',
    'G#m': '4A', 'Abm': '4A', 'G#min': '4A', 'Ab minor': '4A', 'Ab Minor': '4A', 'Abmin': '4A', 'G# minor': '4A',

    // ── Camelot codes as input (passthrough) ──
    '1A': '1A', '2A': '2A', '3A': '3A', '4A': '4A', '5A': '5A', '6A': '6A',
    '7A': '7A', '8A': '8A', '9A': '9A', '10A': '10A', '11A': '11A', '12A': '12A',
    '1B': '1B', '2B': '2B', '3B': '3B', '4B': '4B', '5B': '5B', '6B': '6B',
    '7B': '7B', '8B': '8B', '9B': '9B', '10B': '10B', '11B': '11B', '12B': '12B',

    // ── OpenKey format (1m=minor, 1d=major) ──
    '1m': '1A', '2m': '2A', '3m': '3A', '4m': '4A', '5m': '5A', '6m': '6A',
    '7m': '7A', '8m': '8A', '9m': '9A', '10m': '10A', '11m': '11A', '12m': '12A',
    '1d': '1B', '2d': '2B', '3d': '3B', '4d': '4B', '5d': '5B', '6d': '6B',
    '7d': '7B', '8d': '8B', '9d': '9B', '10d': '10B', '11d': '11B', '12d': '12B',
}

// Colors for Camelot positions (1-12)
const CAMELOT_COLORS = {
    '1': '#ef4444', '2': '#f97316', '3': '#f59e0b',
    '4': '#eab308', '5': '#84cc16', '6': '#22c55e',
    '7': '#10b981', '8': '#14b8a6', '9': '#06b6d4',
    '10': '#3b82f6', '11': '#8b5cf6', '12': '#c026d3',
}

/**
 * Convert a musical key string to its Camelot code.
 * @param {string} key - e.g. "Am", "C", "Bbm", "F# major", "8A", "3d"
 * @returns {string|null} e.g. "8A", "8B" or null
 */
export function keyToCamelot(key) {
    if (!key || key === '?' || key === 'Unknown') return null
    const trimmed = key.trim()
    return KEY_TO_CAMELOT[trimmed] || null
}

/**
 * Parse Camelot code into number + letter.
 * @param {string} code - e.g. "8A"
 * @returns {{ num: number, letter: string }|null}
 */
function parseCamelot(code) {
    if (!code) return null
    const match = code.match(/^(\d{1,2})([AB])$/)
    if (!match) return null
    return { num: parseInt(match[1]), letter: match[2] }
}

/**
 * Get the color for a Camelot code.
 * @param {string} code
 * @returns {string} hex color
 */
export function camelotColor(code) {
    const parsed = parseCamelot(code)
    if (!parsed) return '#ffffff20'
    return CAMELOT_COLORS[parsed.num] || '#ffffff20'
}

/**
 * Check if two Camelot codes are harmonically compatible.
 * Rules: same code, ±1 on wheel (wraps 12→1), or same number A↔B switch.
 * @param {string} code1
 * @param {string} code2
 * @returns {boolean}
 */
export function isCompatible(code1, code2) {
    const a = parseCamelot(code1)
    const b = parseCamelot(code2)
    if (!a || !b) return false

    // Same code
    if (a.num === b.num && a.letter === b.letter) return true

    // Same number, A↔B switch (relative major/minor)
    if (a.num === b.num && a.letter !== b.letter) return true

    // ±1 on wheel, same letter (adjacent key)
    if (a.letter === b.letter) {
        const diff = Math.abs(a.num - b.num)
        if (diff === 1 || diff === 11) return true // 11 = wrap (12→1)
    }

    return false
}

/**
 * Get all compatible Camelot codes for a given code.
 * @param {string} code
 * @returns {string[]}
 */
export function getCompatibleCodes(code) {
    const parsed = parseCamelot(code)
    if (!parsed) return []
    const { num, letter } = parsed
    const results = [code]

    // A↔B switch
    results.push(`${num}${letter === 'A' ? 'B' : 'A'}`)

    // ±1 same letter
    const prev = num === 1 ? 12 : num - 1
    const next = num === 12 ? 1 : num + 1
    results.push(`${prev}${letter}`)
    results.push(`${next}${letter}`)

    return results
}

/**
 * Composable: use Camelot wheel utilities.
 */
export function useCamelot() {
    return {
        keyToCamelot,
        camelotColor,
        isCompatible,
        getCompatibleCodes,
    }
}
