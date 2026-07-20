/**
 * Application shell: sidebar navigation, header and content region.
 *
 * Rendered as the parent route, so the sidebar keeps its state while the page
 * inside the `<Outlet />` changes.
 */

import { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { History as HistoryIcon, Image as ImageIcon, Menu, ScanLine, Video, X } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

/** One entry in the sidebar. */
interface NavigationItem {
  /** Router path. */
  to: string;
  /** Vietnamese label shown to the user. */
  label: string;
  /** Short explanation shown in the header under the page title. */
  description: string;
  icon: LucideIcon;
}

/**
 * The three destinations of the application.
 *
 * Also drives the header title, so a route and its label can never disagree.
 */
const NAVIGATION_ITEMS: readonly NavigationItem[] = [
  {
    to: '/',
    label: 'Nhận dạng ảnh',
    description: 'Tải ảnh lên và nhận dạng biển số',
    icon: ImageIcon,
  },
  {
    to: '/video',
    label: 'Nhận dạng video',
    description: 'Tải video lên, xử lý nền và theo dõi tiến độ',
    icon: Video,
  },
  {
    to: '/history',
    label: 'Lịch sử',
    description: 'Tra cứu, lọc và quản lý kết quả đã lưu',
    icon: HistoryIcon,
  },
];

/**
 * Find the navigation entry matching the current URL.
 *
 * The root path is matched exactly; every other entry matches its own path and
 * anything nested under it, so future detail routes still resolve to a title.
 *
 * @param pathname - Current location pathname.
 * @returns The matching entry, or the dashboard entry as a fallback.
 */
function findActiveItem(pathname: string): NavigationItem {
  const match = NAVIGATION_ITEMS.find(
    (item) =>
      item.to !== '/' &&
      (pathname === item.to || pathname.startsWith(`${item.to}/`)),
  );
  // NAVIGATION_ITEMS is a non-empty literal, but `noUncheckedIndexedAccess`
  // makes the index access optional, hence the explicit fallback.
  return match ?? NAVIGATION_ITEMS[0]!;
}

/**
 * Compose the CSS classes for a sidebar link.
 *
 * @param isActive - Whether the link points at the current route.
 * @returns The class string.
 */
function navLinkClasses(isActive: boolean): string {
  const base =
    'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors';
  return isActive
    ? `${base} bg-primary text-white shadow-sm`
    : `${base} text-content-muted hover:bg-surface-raised hover:text-content`;
}

/**
 * Render the shared page frame.
 *
 * @returns The layout with the active page in its content region.
 */
export default function Layout(): JSX.Element {
  const location = useLocation();
  const activeItem = findActiveItem(location.pathname);
  // Sidebar is permanent from `lg` up; below that it is a toggleable drawer.
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const closeSidebar = (): void => setIsSidebarOpen(false);

  return (
    <div className="min-h-screen bg-surface-muted">
      {/* Backdrop, mobile only: tapping outside dismisses the drawer. */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-content/40 lg:hidden"
          onClick={closeSidebar}
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-border
                    bg-surface transition-transform duration-200 lg:translate-x-0
                    ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="flex h-16 items-center gap-2.5 border-b border-border px-5">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-white">
            <ScanLine size={20} aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold leading-tight">
              Nhận dạng biển số
            </p>
            <p className="truncate text-xs text-content-muted">Phiên bản 0.1.0</p>
          </div>
          <button
            type="button"
            onClick={closeSidebar}
            className="ml-auto rounded-md p-1 text-content-muted hover:bg-surface-raised lg:hidden"
            aria-label="Đóng menu"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto p-3" aria-label="Điều hướng chính">
          {NAVIGATION_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={closeSidebar}
              className={({ isActive }) => navLinkClasses(isActive)}
            >
              <Icon size={18} aria-hidden="true" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-border p-4">
          <p className="text-xs leading-relaxed text-content-muted">
            Đồ án tốt nghiệp
            <br />
            YOLO11 + PaddleOCR · Suy luận trên CPU
          </p>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-border bg-surface/95 px-5 backdrop-blur">
          <button
            type="button"
            onClick={() => setIsSidebarOpen(true)}
            className="rounded-md p-2 text-content-muted hover:bg-surface-raised lg:hidden"
            aria-label="Mở menu"
          >
            <Menu size={20} aria-hidden="true" />
          </button>

          <div className="min-w-0">
            <h1 className="truncate text-base font-semibold leading-tight">
              {activeItem.label}
            </h1>
            <p className="truncate text-xs text-content-muted">
              {activeItem.description}
            </p>
          </div>
        </header>

        <main className="animate-fade-in p-5 lg:p-7">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
