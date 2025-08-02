import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'build',
    // Ensure assets are prefixed with /static
    assetsDir: 'assets'
  },
  server: {
    port: 5173
  },
  base: '/'
})