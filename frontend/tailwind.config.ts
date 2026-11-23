import type { Config } from 'tailwindcss'

export default {
    content: [
        './app/**/*.vue',
        './components/**/*.vue',
        './layouts/**/*.vue',
        './pages/**/*.vue',
    ],
    theme: {
        extend: {
            colors: {
                // Nebula Console — Design Tokens
                nebula: {
                    void: '#09090b',    // Fondo principal — el vacío del espacio
                    deep: '#0c0c10',    // Superficie base — oscuridad con azul implícito
                    surface: '#12121a', // Elevación 1 — apenas distinguible
                    raised: '#1a1a26',  // Elevación 2 — paneles flotantes
                    border: 'rgba(255, 255, 255, 0.06)', // Bordes sutiles
                },
                pulse: {
                    DEFAULT: '#06b6d4', // Cyan eléctrico — acento primario
                    dim: '#0891b2',
                    glow: '#22d3ee',
                    muted: 'rgba(6, 182, 212, 0.15)',
                    ghost: 'rgba(6, 182, 212, 0.06)',
                },
                laser: {
                    DEFAULT: '#c026d3', // Magenta laser — selección, alta energía
                    dim: '#a21caf',
                    glow: '#e879f9',
                    muted: 'rgba(192, 38, 211, 0.15)',
                },
                vu: {
                    DEFAULT: '#f59e0b', // Ámbar VU meter — datos numéricos
                    dim: '#d97706',
                    glow: '#fbbf24',
                    muted: 'rgba(245, 158, 11, 0.15)',
                },
                // Texto jerárquico
                ink: {
                    primary: 'rgba(255, 255, 255, 0.92)',
                    secondary: 'rgba(255, 255, 255, 0.55)',
                    tertiary: 'rgba(255, 255, 255, 0.32)',
                    muted: 'rgba(255, 255, 255, 0.16)',
                },
            },
            fontFamily: {
                display: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
                data: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
            },
            borderRadius: {
                'sm': '6px',
                'md': '10px',
                'lg': '14px',
                'xl': '20px',
            },
            animation: {
                'breathe': 'breathe 4s ease-in-out infinite',
                'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
                'fade-in': 'fadeIn 0.3s ease-out',
                'slide-up': 'slideUp 0.4s ease-out',
                'nebula-1': 'nebula1 6s ease-in-out infinite',
                'nebula-2': 'nebula2 8s ease-in-out infinite',
                'nebula-3': 'nebula3 10s ease-in-out infinite',
                'nebula-4': 'nebula4 7s ease-in-out infinite',
            },
            keyframes: {
                breathe: {
                    '0%, 100%': { opacity: '0.4' },
                    '50%': { opacity: '0.8' },
                },
                pulseGlow: {
                    '0%, 100%': { boxShadow: '0 0 8px 0 rgba(6, 182, 212, 0.3)' },
                    '50%': { boxShadow: '0 0 20px 4px rgba(6, 182, 212, 0.5)' },
                },
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { opacity: '0', transform: 'translateY(12px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                nebula1: {
                    '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: '0.12' },
                    '50%': { transform: 'translate(5%, 8%) scale(1.15)', opacity: '0.22' },
                },
                nebula2: {
                    '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: '0.10' },
                    '50%': { transform: 'translate(-6%, -5%) scale(1.2)', opacity: '0.20' },
                },
                nebula3: {
                    '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: '0.08' },
                    '50%': { transform: 'translate(4%, -6%) scale(1.1)', opacity: '0.18' },
                },
                nebula4: {
                    '0%, 100%': { transform: 'translate(0, 0) scale(1)', opacity: '0.06' },
                    '50%': { transform: 'translate(-3%, 4%) scale(1.12)', opacity: '0.14' },
                },
            },
        },
    },
    plugins: [],
} satisfies Config
