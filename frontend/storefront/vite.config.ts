import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    // Keep the local @ofs/shared package inside this app's dependency tree so
    // React resolves to the same installation for the app and shared package.
    preserveSymlinks: true,
  },
  server: {
    port: 5173,
    proxy: {
      // Flask backend runs on :5000 in dev; matches the /api/* routes from the LLD.
      '/api': 'http://localhost:5000',
    },
  },
})
