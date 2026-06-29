import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite dev server runs on port 5173 (the origin we allowed in the backend CORS).
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
})
