import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    // Los mocks de MSW (src/test/mocks/handlers.ts) responden en esta URL;
    // fijarla aquí evita depender del .env.local de cada máquina (y de CI).
    env: { VITE_API_URL: 'http://localhost:8000' },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
    },
  },
})
