/**
 * Route table for the application.
 *
 * Three pages sit inside the shared {@link Layout}, which renders the sidebar
 * and header around an `<Outlet />`. Image detection is the index route — the
 * screen a demo opens on — and any unknown path redirects there rather than
 * showing a dead end.
 *
 * Each page is loaded on demand. Only one of the three is ever on screen, and
 * the video page in particular carries code the other pages never need, so
 * loading everything up front only delays the first paint. The `<Suspense>`
 * boundary sits *inside* the layout route, which means the sidebar and header
 * stay mounted while a page's chunk arrives — the shell never flickers, only
 * the content region does.
 */

import { lazy, Suspense } from 'react';
import type { ReactNode } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import Layout from '@/components/Layout';
import { Skeleton } from '@/components/ui';

const History = lazy(() => import('@/pages/History'));
const ImageDetection = lazy(() => import('@/pages/ImageDetection'));
const VideoDetection = lazy(() => import('@/pages/VideoDetection'));

/**
 * Placeholder shown while a page chunk is being fetched.
 *
 * Given a fixed minimum height on purpose: a fallback that collapses to its
 * content height would let the page grow abruptly the instant the real content
 * mounts, which reads as a glitch during a live demonstration.
 *
 * @returns The placeholder block.
 */
function RouteFallback(): JSX.Element {
  return (
    <div className="min-h-[70vh] space-y-5" aria-busy="true">
      <Skeleton className="h-24 w-full" rounded="lg" />
      <Skeleton className="h-64 w-full" rounded="lg" />
    </div>
  );
}

/**
 * Wrap a lazily loaded page element in its own suspense boundary.
 *
 * Per route rather than once around `<Routes>`: a single outer boundary would
 * unmount the layout — sidebar included — every time a page changed.
 *
 * @param element - The page element to render once its chunk is available.
 * @returns The element, guarded by a suspense boundary.
 */
function withSuspense(element: ReactNode): JSX.Element {
  return <Suspense fallback={<RouteFallback />}>{element}</Suspense>;
}

/**
 * Root component: declares the routes.
 *
 * @returns The routed application tree.
 */
export default function App(): JSX.Element {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={withSuspense(<ImageDetection />)} />
        <Route path="video" element={withSuspense(<VideoDetection />)} />
        <Route path="history" element={withSuspense(<History />)} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
