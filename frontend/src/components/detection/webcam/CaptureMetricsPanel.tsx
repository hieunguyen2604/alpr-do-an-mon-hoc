/**
 * Live capture measurements.
 *
 * On screen rather than in a console because NFR-P2 is written in frames per
 * second: a number nobody can see during a demo cannot be quoted in an
 * evaluation. The two timing figures are deliberately separate — the server's
 * own `processing_time` next to the browser-measured round trip — because
 * their difference is exactly the transfer and queueing overhead, and that is
 * the first thing worth knowing when the loop feels slow.
 */

import { Activity, Gauge, Layers, Timer } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

import { formatNumber, formatProcessingTime, NO_VALUE } from '@/lib/format';

import type { CaptureMetrics } from './types';

/** Props of {@link CaptureMetricsPanel}. */
export interface CaptureMetricsPanelProps {
  metrics: CaptureMetrics;
  /** Session id shared by every frame, shown so a demo can be traced. */
  jobId: string | null;
}

/** Props of {@link MetricTile}. */
interface MetricTileProps {
  icon: LucideIcon;
  label: string;
  value: string;
  hint?: string;
}

/**
 * One measurement, as a compact tile.
 *
 * @param props - Icon, label, value and an optional secondary line.
 * @returns The tile.
 */
function MetricTile({ icon: Icon, label, value, hint }: MetricTileProps): JSX.Element {
  return (
    <div className="rounded-lg border border-border bg-surface-muted px-3.5 py-3">
      <div className="flex items-center gap-1.5 text-xs text-content-muted">
        <Icon size={13} aria-hidden="true" />
        <span>{label}</span>
      </div>
      <p className="mt-1 text-lg font-semibold tabular-nums text-content">{value}</p>
      {hint && <p className="mt-0.5 text-xs text-content-muted">{hint}</p>}
    </div>
  );
}

/**
 * Render the metrics panel.
 *
 * @param props - The measurements and the session id.
 * @returns The panel.
 */
export function CaptureMetricsPanel({
  metrics,
  jobId,
}: CaptureMetricsPanelProps): JSX.Element {
  const fpsText =
    metrics.fps === null
      ? NO_VALUE
      : `${metrics.fps.toLocaleString('vi-VN', {
          minimumFractionDigits: 1,
          maximumFractionDigits: 1,
        })} FPS`;

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <MetricTile
          icon={Gauge}
          label="Tốc độ thực tế"
          value={fpsText}
          hint="Đo trong 5 giây gần nhất"
        />
        <MetricTile
          icon={Timer}
          label="Thời gian xử lý"
          value={formatProcessingTime(metrics.lastProcessingTimeSeconds)}
          hint={`Trung bình ${formatProcessingTime(metrics.averageProcessingTimeSeconds)}`}
        />
        <MetricTile
          icon={Activity}
          label="Trọn vòng gửi–nhận"
          value={formatProcessingTime(metrics.lastRoundTripSeconds)}
          hint="Gồm cả thời gian truyền tải"
        />
        <MetricTile
          icon={Layers}
          label="Khung hình đã gửi"
          value={formatNumber(metrics.framesSent)}
          hint={`Bỏ qua ${formatNumber(metrics.framesSkipped)} khung`}
        />
      </div>

      <p className="text-xs text-content-muted">
        Khung hình bị bỏ qua khi khung trước chưa xử lý xong — đây là cơ chế cố ý
        để độ trễ không dồn lại.
        {jobId && (
          <>
            {' '}
            Mã phiên:{' '}
            <span className="font-mono text-content">{jobId}</span>
          </>
        )}
      </p>
    </div>
  );
}

export default CaptureMetricsPanel;
