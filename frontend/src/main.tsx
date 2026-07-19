/**
 * Application entry point.
 *
 * Mounts the React tree into the `#root` element declared in `index.html` and
 * installs the router. Everything below this file is routing and UI.
 */

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';

import App from '@/App';
import '@/index.css';

const container = document.getElementById('root');

// A missing container means index.html and this file have drifted apart.
// Failing loudly here is far easier to diagnose than a silently blank page.
if (!container) {
  throw new Error(
    'Root element #root not found. Check that index.html contains <div id="root"></div>.',
  );
}

createRoot(container).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
