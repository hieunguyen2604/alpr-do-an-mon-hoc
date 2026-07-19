/**
 * Service readiness, from `GET /health`.
 *
 * The model-loaded flag is the reason this card is prominent rather than tucked
 * into a footer. When the weights are missing the API still answers every
 * detection request with a perfectly well-formed 200 — the results are simply
 * fabricated by a stub pipeline. Nothing in a detection response reveals that,
 * so the health endpoint is the *only* place a user can learn that the plate
 * numbers on screen are not real. Hiding or softening it would let someone read
 * simulated output as a measurement.
 */

import { AlertTriangle, CheckCircle2, Database, XCircle } from 'lucide-react';

import { Badge } from '@/components/ui';
import { Skeleton } from '@/components/ui';
import type { HealthStatus } from '@/types';

/** Props of {@link SystemStatusCard}. */
export interface SystemStatusCardProps {
  /** Health payload, or `null` before the first successful check. */
  health: HealthStatus | null;
  isLoading?: boolean;
  /** Display-ready Vietnamese message when the health check itself failed. */
  error?: string | null;
}

/** Props of {@link StatusRow}. */
interface StatusRowProps {
  icon: JSX.Element;
  label: string;
  isHealthy: boolean;
  healthyText: string;
  unhealthyText: string;
}

/**
 * One labelled readiness indicator.
 *
 * The state is written out in words next to the badge, so it is never carried
 * by colour alone (NFR-U5).
 *
 * @param props - Icon, label and the two possible readings.
 * @returns The indicator row.
 */
function StatusRow({
  icon,
  label,
  isHealthy,
  healthyText,
  unhealthyText,
}: StatusRowProps): JSX.Element {
  return (
    <div className="flex items-center justify-between gap-3 py-1.5">
      <span className="inline-flex items-center gap-2 text-sm text-content-muted">
        {icon}
        {label}
      </span>
      <Badge
        variant={isHealthy ? 'success' : 'warning'}
        icon={
          isHealthy ? (
            <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
          ) : (
            <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />
          )
        }
      >
        {isHealthy ? healthyText : unhealthyText}
      </Badge>
    </div>
  );
}

/**
 * Render the system status card.
 *
 * @param props - Health payload, loading flag and any check error.
 * @returns The status card.
 */
export function SystemStatusCard({
  health,
  isLoading = false,
  error = null,
}: SystemStatusCardProps): JSX.Element {
  return (
    <section className="card-padded" aria-labelledby="system-status-heading">
      <h2
        id="system-status-heading"
        className="text-sm font-semibold text-content"
      >
        Trạng thái hệ thống
      </h2>

      {isLoading ? (
        <div className="mt-3 space-y-2.5" aria-busy="true">
          <Skeleton className="h-6 w-full" />
          <Skeleton className="h-6 w-full" />
        </div>
      ) : error ? (
        // A failed health check is reported, never assumed healthy: silently
        // showing green here would be worse than showing nothing.
        <div
          className="mt-3 flex items-start gap-2.5 rounded-lg border border-danger/30
                     bg-danger/5 px-3 py-2.5"
          role="alert"
        >
          <XCircle
            className="mt-0.5 h-4 w-4 shrink-0 text-danger"
            aria-hidden="true"
          />
          <p className="text-sm text-content">
            Không kiểm tra được trạng thái hệ thống. {error}
          </p>
        </div>
      ) : health ? (
        <>
          <div className="mt-2 divide-y divide-border">
            <StatusRow
              icon={<Database className="h-4 w-4" aria-hidden="true" />}
              label="Cơ sở dữ liệu"
              isHealthy={health.database_connected}
              healthyText="Đã kết nối"
              unhealthyText="Mất kết nối"
            />
            <StatusRow
              icon={<CheckCircle2 className="h-4 w-4" aria-hidden="true" />}
              label="Mô hình AI"
              isHealthy={health.model_loaded}
              healthyText="Đã nạp"
              unhealthyText="Chưa nạp"
            />
          </div>

          {!health.model_loaded && (
            <div
              className="mt-3 flex items-start gap-2.5 rounded-lg border border-warning/40
                         bg-warning/10 px-3 py-2.5"
              role="alert"
            >
              <AlertTriangle
                className="mt-0.5 h-4 w-4 shrink-0 text-warning"
                aria-hidden="true"
              />
              <div>
                <p className="text-sm font-medium text-content">
                  Hệ thống đang chạy ở chế độ mô phỏng (chưa nạp mô hình AI)
                </p>
                <p className="mt-1 text-xs leading-relaxed text-content-muted">
                  Các biển số hiển thị trên trang này là kết quả giả lập, không
                  phải kết quả nhận dạng thật. Số liệu thống kê vẫn được ghi nhận
                  bình thường.
                </p>
              </div>
            </div>
          )}

          {!health.database_connected && (
            <div
              className="mt-3 flex items-start gap-2.5 rounded-lg border border-danger/30
                         bg-danger/5 px-3 py-2.5"
              role="alert"
            >
              <XCircle
                className="mt-0.5 h-4 w-4 shrink-0 text-danger"
                aria-hidden="true"
              />
              <p className="text-sm text-content">
                Mất kết nối cơ sở dữ liệu — kết quả nhận dạng có thể không được
                lưu lại.
              </p>
            </div>
          )}
        </>
      ) : null}
    </section>
  );
}

export default SystemStatusCard;
