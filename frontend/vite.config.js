import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backendPort = env.VITE_BACKEND_PORT || '8000'
  const backendUrl = `http://localhost:${backendPort}`
  const backendWs = `ws://localhost:${backendPort}`

  return {
    plugins: [
      vue(),
      tailwindcss(),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: backendUrl,
          changeOrigin: true,
        },
        '/ws': {
          target: backendWs,
          ws: true,
          changeOrigin: true,
        },
        '/storage': {
          target: backendUrl,
          changeOrigin: true,
        },
        '/stream-proxy': {
          target: 'https://mitradarat-vidstream.dephub.go.id',
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/stream-proxy/, ''),
        },
      },
    },
    build: {
      outDir: '../backend/static',
      emptyOutDir: true,
    },
  }
})