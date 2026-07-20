/**
 * Route table for the application.
 *
 * Five pages sit inside the shared {@link Layout}, which renders the sidebar
 * and header around an `<Outlet />`. Any unknown path redirects to the
 * dashboard rather than showing a dead end.
 *
 * Each page is loaded on demand. Only one of the five is ever on screen, and
 * the webcam and video pages in particular carry code the dashboard never
 * needs, so loading all five up front only delays the first paint. The
 * `<Suspense>` boundary sits *inside* the layout route, which means the sidebar
 * and header stay mounted while a page's chunk arrives — the shell never
 * flickers, only the content region does.
 */

import { lazy, Suspense } from 'react';
import type { ReactNode } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import Layout from '@/components/Layout';
import { Skeleton } from '@/components/ui';

const Dashboard = lazy(() => import('@/pages/Dashboard'));
const History = lazy(() => import('@/pages/History'));
const ImageDetection = lazy(() => import('@/pages/ImageDetection'));
const VideoDetection = lazy(() => import('@/pages/VideoDetection'));
const WebcamDetection = lazy(() => import('@/pages/WebcamDetection'));

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
        <Route index element={withSuspense(<Dashboard />)} />
        <Route path="image" element={withSuspense(<ImageDetection />)} />
        <Route path="video" element={withSuspense(<VideoDetection />)} />
        <Route path="webcam" element={withSuspense(<WebcamDetection />)} />
        <Route path="history" element={withSuspense(<History />)} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
