import {defineConfig} from 'vite'
import react from '@vitejs/plugin-react'
import {VitePWA} from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
    plugins: [
        react(),
        VitePWA({
            registerType: 'autoUpdate',
            includeAssets: ['favicon.ico', 'piggy.svg', 'fonts/*.ttf'],
            manifest: {
                name: 'Piggy Budget Planner',
                short_name: 'Piggy',
                description: 'Your elegant personal finance and budget planner',
                theme_color: '#7DB9E8',
                background_color: '#E3F2FD',
                display: 'standalone',
                icons: [
                    {
                        src: 'piggy.svg',
                        sizes: 'any',
                        type: 'image/svg+xml',
                        purpose: 'any'
                    },
                    {
                        src: 'piggy.svg',
                        sizes: '192x192',
                        type: 'image/svg+xml',
                        purpose: 'maskable'
                    },
                    {
                        src: 'piggy.svg',
                        sizes: '512x512',
                        type: 'image/svg+xml',
                        purpose: 'maskable'
                    }
                ]
            },
            devOptions: {
                enabled: true
            }
        })
    ],
    server: {
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            }
        }
    }
})
