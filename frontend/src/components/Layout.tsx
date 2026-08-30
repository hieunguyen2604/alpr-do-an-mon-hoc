/**
 * Application shell: sidebar navigation, header with theme switch, and content region.
 */

import { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  Camera,
  History as HistoryIcon,
  Image as ImageIcon,
  Menu,
  Moon,
  ScanLine,
  Sun,
  Video,
  X,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface NavigationItem {
  to: string;
  label: string;
  description: string;
  icon: LucideIcon;
}

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
    to: '/webcam',
    label: 'Quét Webcam trực tiếp',
    description: 'Nhận dạng biển số thời gian thực qua camera laptop',
    icon: Camera,
  },
  {
    to: '/history',
    label: 'Lịch sử',
    description: 'Tra cứu, lọc và quản lý kết quả đã lưu',
    icon: HistoryIcon,
  },
];

function findActiveItem(pathname: string): NavigationItem {
  const match = NAVIGATION_ITEMS.find(
    (item) =>
      item.to !== '/' &&
      (pathname === item.to || pathname.startsWith(`${item.to}/`)),
  );
  return match ?? NAVIGATION_ITEMS[0]!;
}

function navLinkClasses(isActive: boolean): string {
  const base =
    'flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-200';
  return isActive
    ? `${base} bg-primary text-slate-950 font-semibold shadow-md shadow-primary/20`
    : `${base} text-content-muted hover:bg-surface-raised hover:text-content`;
}

export default function Layout(): JSX.Element {
  const location = useLocation();
  const activeItem = findActiveItem(location.pathname);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Dark mode state: default to true (Deep Navy theme)
  const [isDark, setIsDark] = useState<boolean>(() => {
    const saved = localStorage.getItem('alpr_theme');
    if (saved !== null) {
      return saved === 'dark';
    }
    return true; // Default to dark theme
  });

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('alpr_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('alpr_theme', 'light');
    }
  }, [isDark]);

  const toggleTheme = () => setIsDark((prev) => !prev);
  const closeSidebar = (): void => setIsSidebarOpen(false);

  return (
    <div className="min-h-screen bg-surface-muted transition-colors duration-200">
      {/* Backdrop for mobile */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={closeSidebar}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-border
                    bg-surface transition-transform duration-200 lg:translate-x-0
                    ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="flex h-16 items-center gap-3 border-b border-border px-5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-slate-950 shadow-md shadow-primary/20 font-bold">
            <ScanLine size={20} aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-bold tracking-tight">
              ALPR VIỆT NAM
            </p>
            <p className="truncate text-[11px] text-content-muted">ĐATN · YOLO11 + PaddleOCR</p>
          </div>
          <button
            type="button"
            onClick={closeSidebar}
            className="ml-auto rounded-lg p-1 text-content-muted hover:bg-surface-raised lg:hidden"
            aria-label="Đóng menu"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <nav className="flex-1 space-y-1.5 overflow-y-auto p-3" aria-label="Điều hướng chính">
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
          <div className="rounded-xl border border-border/60 bg-surface-raised/50 p-3 text-xs leading-relaxed text-content-muted">
            <p className="font-semibold text-content">Nhận dạng Biển số xe</p>
            <p className="mt-0.5 text-[11px]">Chuẩn TT 79/2024 · Biển 1 & 2 dòng</p>
          </div>
        </div>
      </aside>

      {/* Main Content Frame */}
      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-border bg-surface/90 px-5 backdrop-blur-md">
          <div className="flex items-center gap-3 min-w-0">
            <button
              type="button"
              onClick={() => setIsSidebarOpen(true)}
              className="rounded-lg p-2 text-content-muted hover:bg-surface-raised lg:hidden"
              aria-label="Mở menu"
            >
              <Menu size={20} aria-hidden="true" />
            </button>

            <div className="min-w-0">
              <h1 className="truncate text-base font-bold leading-tight text-content">
                {activeItem.label}
              </h1>
              <p className="truncate text-xs text-content-muted">
                {activeItem.description}
              </p>
            </div>
          </div>

          {/* Theme Toggle Button */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={toggleTheme}
              className="flex h-9 w-9 items-center justify-center rounded-xl border border-border bg-surface-raised text-content hover:border-primary/50 transition-colors shadow-sm"
              title={isDark ? 'Chuyển sang giao diện Sáng' : 'Chuyển sang giao diện Tối (Deep Navy)'}
              aria-label="Đổi giao diện"
            >
              {isDark ? (
                <Sun size={18} className="text-amber-400" />
              ) : (
                <Moon size={18} className="text-slate-700" />
              )}
            </button>
          </div>
        </header>

        <main className="animate-fade-in p-5 lg:p-7">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
