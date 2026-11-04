import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // API_URL=http://localhost:5001 points the proxy elsewhere (macOS AirPlay uses :5000).
  const apiUrl = loadEnv(mode, '.', 'API_').API_URL ?? 'http://localhost:5000'
  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      dedupe: ['react', 'react-dom', 'react-router-dom'],
    },
    server: {
      port: 5174, // different port than storefront so both can run at once
      proxy: {
        '/api': apiUrl,
      },
    },
  }
})
