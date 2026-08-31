/** Route table for the application (loads pages lazily to avoid blocking first paint). */

import { lazy, Suspense } from 'react';
import type { ReactNode } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import Layout from '@/components/Layout';
import { Skeleton } from '@/components/ui';

const History = lazy(() => import('@/pages/History'));
const ImageDetection = lazy(() => import('@/pages/ImageDetection'));
const VideoDetection = lazy(() => import('@/pages/VideoDetection'));
const WebcamDetection = lazy(() => import('@/pages/WebcamDetection'));

/** Placeholder shown while a lazily loaded page chunk is being fetched. */
function RouteFallback(): JSX.Element {
  return (
    <div className="min-h-[70vh] space-y-5" aria-busy="true">
      <Skeleton className="h-24 w-full" rounded="lg" />
      <Skeleton className="h-64 w-full" rounded="lg" />
    </div>
  );
}

/** Wrap a lazily loaded page element in its own suspense boundary. */
function withSuspense(element: ReactNode): JSX.Element {
  return <Suspense fallback={<RouteFallback />}>{element}</Suspense>;
}

/** Root component: declares the routes. */
export default function App(): JSX.Element {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={withSuspense(<ImageDetection />)} />
        <Route path="video" element={withSuspense(<VideoDetection />)} />
        <Route path="webcam" element={withSuspense(<WebcamDetection />)} />
        <Route path="history" element={withSuspense(<History />)} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
