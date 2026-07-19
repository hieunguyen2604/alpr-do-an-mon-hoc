/**
 * The dashboard's headline figures (FR-4.1).
 *
 * The first two tiles are the reason this component takes care over its
 * wording. `total_jobs` counts **uploads** and `total_detections` counts
 * **license plates**; an image containing three plates is one upload and three
 * plates. Presenting either as "số lần nhận dạng" without qualification makes
 * the two interchangeable in the reader's mind, and the resulting figure is
 * wrong in a way that still looks reasonable.
 *
 * So the labels name different things ("Lượt nhận dạng" vs "Biển số phát
 * hiện"), each carries a hint, and each hint carries a tooltip spelling the
 * relationship out with an example.
 */

import { Gauge, Layers, Timer, Upload } from 'lucide-react';

import { StatCard } from '@/components/ui';
import { formatDuration, formatNumber, formatPercent } from '@/lib/format';
import type { Statistics } from '@/types';

import { InfoTooltip } from './InfoTooltip';

/** Props of {@link StatisticsCards}. */
export interface StatisticsCardsProps {
  /** Aggregates from `GET /api/statistics`, or `null` while loading. */
  statistics: Statistics | null;
  /** Render placeholders instead of figures. */
  isLoading?: boolean;
}

/**
 * Render the four headline metric tiles.
 *
 * @param props - The statistics payload and the loading flag.
 * @returns The tile grid.
 */
export function StatisticsCards({
  statistics,
  isLoading = false,
}: StatisticsCardsProps): JSX.Element {
  return (
    // Two columns at 1366px and four on a wide monitor. The tiles never drop to
    // a single column above the supported minimum width (NFR-U4).
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard
        label="Lượt nhận dạng"
        value={formatNumber(statistics?.total_jobs)}
        icon={<Upload size={18} aria-hidden="true" />}
        tone="primary"
        isLoading={isLoading}
        hint={
          <span className="inline-flex items-center gap-1">
            Số tệp đã tải lên và xử lý
            <InfoTooltip
              label="Giải thích: Lượt nhận dạng"
              text="Mỗi lần tải lên một ảnh, một video hoặc một phiên webcam được tính là một lượt — bất kể trong đó có bao nhiêu biển số."
            />
          </span>
        }
      />

      <StatCard
        label="Biển số phát hiện"
        value={formatNumber(statistics?.total_detections)}
        icon={<Layers size={18} aria-hidden="true" />}
        tone="success"
        isLoading={isLoading}
        hint={
          <span className="inline-flex items-center gap-1">
            Tổng số biển số đọc được
            <InfoTooltip
              label="Giải thích: Biển số phát hiện"
              text="Đếm theo từng biển số, không phải theo tệp. Một ảnh chứa 3 biển số được tính là 1 lượt nhận dạng nhưng 3 biển số phát hiện."
            />
          </span>
        }
      />

      <StatCard
        label="Độ tin cậy trung bình"
        value={formatPercent(statistics?.average_confidence)}
        icon={<Gauge size={18} aria-hidden="true" />}
        tone="primary"
        isLoading={isLoading}
        hint={
          <span className="inline-flex items-center gap-1">
            {`Bước phát hiện · OCR ${formatPercent(statistics?.average_ocr_confidence)}`}
            <InfoTooltip
              label="Giải thích: Độ tin cậy trung bình"
              text="Số lớn là độ tin cậy của bước phát hiện biển số (YOLO). Độ tin cậy của bước đọc ký tự (OCR) được ghi kèm bên cạnh — hai bước được đo riêng để biết bước nào kém chắc chắn hơn."
            />
          </span>
        }
      />

      <StatCard
        label="Thời gian xử lý trung bình"
        value={formatDuration(statistics?.average_processing_time)}
        icon={<Timer size={18} aria-hidden="true" />}
        tone="warning"
        isLoading={isLoading}
        hint={
          <span className="inline-flex items-center gap-1">
            Trung bình trên mỗi biển số
            <InfoTooltip
              label="Giải thích: Thời gian xử lý trung bình"
              text="Thời gian trung bình để phát hiện và đọc một biển số, tính trên toàn bộ dữ liệu đã xử lý. Suy luận chạy trên CPU nên con số này phụ thuộc vào cấu hình máy chủ."
            />
          </span>
        }
      />
    </div>
  );
}

export default StatisticsCards;
