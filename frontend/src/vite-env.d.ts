/// <reference types="vite/client" />

/** Typed environment variables (only VITE_-prefixed vars exposed to browser). */
interface ImportMetaEnv {
  /** Backend origin, e.g. `http://localhost:8000`. Empty = same-origin. */
  readonly VITE_API_URL?: string;
  /** Former name of `VITE_API_URL`, still honoured. */
  readonly VITE_API_BASE_URL?: string;
  /** Request timeout in milliseconds, as a decimal string. */
  readonly VITE_API_TIMEOUT_MS?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
