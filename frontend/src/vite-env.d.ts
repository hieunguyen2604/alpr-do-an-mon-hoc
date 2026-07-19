/// <reference types="vite/client" />

/**
 * Typed environment variables.
 *
 * Only variables prefixed with `VITE_` are exposed to the browser bundle by
 * Vite. Declaring them here means `import.meta.env.VITE_API_BASE_URL` is
 * type-checked instead of being an implicit `any`.
 */
interface ImportMetaEnv {
  /**
   * Origin of the backend, e.g. `http://localhost:8000`.
   *
   * Empty by default, which keeps every request same-origin and relative so the
   * dev-server proxy (and, in production, the reverse proxy) handles them.
   *
   * This is the **origin**, not the API base: the client appends `/api` itself,
   * because `GET /health` is deliberately mounted outside that prefix.
   */
  readonly VITE_API_URL?: string;
  /** Former name of `VITE_API_URL`, still honoured. */
  readonly VITE_API_BASE_URL?: string;
  /** Request timeout in milliseconds, as a decimal string. */
  readonly VITE_API_TIMEOUT_MS?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
