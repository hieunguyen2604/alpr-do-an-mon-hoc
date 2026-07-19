/**
 * Route table for the application.
 *
 * Five pages sit inside the shared {@link Layout}, which renders the sidebar
 * and header around an `<Outlet />`. Any unknown path redirects to the
 * dashboard rather than showing a dead end.
 */

import { Navigate, Route, Routes } from 'react-router-dom';

import Layout from '@/components/Layout';
import Dashboard from '@/pages/Dashboard';
import History from '@/pages/History';
import ImageDetection from '@/pages/ImageDetection';
import VideoDetection from '@/pages/VideoDetection';
import WebcamDetection from '@/pages/WebcamDetection';

/**
 * Root component: declares the routes.
 *
 * @returns The routed application tree.
 */
export default function App(): JSX.Element {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="image" element={<ImageDetection />} />
        <Route path="video" element={<VideoDetection />} />
        <Route path="webcam" element={<WebcamDetection />} />
        <Route path="history" element={<History />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
