import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite configuration
// - `base` must match the GitHub Pages project path so assets (like the logo) resolve correctly
// - For this repo, the site is served from /WinLink-FYP/
export default defineConfig({
  plugins: [react()],
  base: '/WinLink-FYP/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false
  }
})
