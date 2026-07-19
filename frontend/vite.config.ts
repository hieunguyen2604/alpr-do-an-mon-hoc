import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

/**
 * Vite build and dev-server configuration.
 *
 * The dev server proxies `/api` to the FastAPI backend so the browser only ever
 * talks to a single origin. That keeps CORS out of the development setup and
 * lets the production build be served as static files behind the same host,
 * where the same `/api` prefix is handled by the reverse proxy.
 */
export default defineConfig({
  plugins: [react()],
  resolve: {
    // Absolute imports: `@/services/api` instead of `../../services/api`.
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    // Fail loudly instead of silently moving to another port, so the proxy
    // target documented in the README always matches reality.
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Stored images: source uploads and cropped plates. The backend mounts
      // these at `/files` (see `FILES_URL_PREFIX` in `storage_service.py`), and
      // it is that path which comes back in `image_path` and
      // `plate_image_path`. Without this entry every result thumbnail is a
      // broken image in development.
      '/files': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // The health endpoint sits at the root rather than under `/api`, so that
      // a health check does not move when the API prefix changes. It therefore
      // needs its own proxy entry.
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
