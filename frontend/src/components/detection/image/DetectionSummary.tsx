/** Headline metric cards for completed image detection results. */

import { Cpu, ScanLine, ShieldCheck } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

import { cn } from '@/lib/cn';
import { formatNumber, formatProcessingTime } from '@/lib/format';
import type { DetectionResponse } from '@/types';

export interface DetectionSummaryProps {
  response: DetectionResponse;
  className?: string;
}

interface SummaryItemProps {
  icon: LucideIcon;
  label: string;
  value: string;
  hint?: string;
  colorClass: string;
  bgClass: string;
}

function SummaryItem({
  icon: Icon,
  label,
  value,
  hint,
  colorClass,
  bgClass,
}: SummaryItemProps): JSX.Element {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-border/60 bg-surface-raised/40 p-3.5 shadow-sm">
      <span
        aria-hidden="true"
        className={cn(
          'flex h-10 w-10 shrink-0 items-center justify-center rounded-xl font-bold shadow-inner',
          bgClass,
          colorClass,
        )}
      >
        <Icon className="h-5 w-5" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-content-muted">{label}</p>
        <p className="text-base font-bold tracking-tight tabular-nums text-content">{value}</p>
        {hint && <p className="text-[11px] text-content-muted truncate">{hint}</p>}
      </div>
    </div>
  );
}

export function DetectionSummary({
  response,
  className,
}: DetectionSummaryProps): JSX.Element {
  const readableCount = response.results.filter(
    (result) => result.plate_number !== null,
  ).length;
  const validCount = response.results.filter(
    (result) => result.is_valid_format && result.plate_number !== null,
  ).length;

  return (
    <div
      className={cn(
        'grid grid-cols-1 gap-3 sm:grid-cols-3',
        className,
      )}
    >
      <SummaryItem
        icon={ScanLine}
        label="Biển số phát hiện"
        value={`${formatNumber(response.plate_count)} biển`}
        hint="Đã khoanh vùng YOLO"
        colorClass="text-sky-400"
        bgClass="bg-sky-500/10 border border-sky-500/20"
      />
      <SummaryItem
        icon={ShieldCheck}
        label="Đọc ký tự OCR"
        value={`${formatNumber(readableCount)}/${formatNumber(response.plate_count)}`}
        hint={`${formatNumber(validCount)} biển chuẩn định dạng`}
        colorClass="text-emerald-400"
        bgClass="bg-emerald-500/10 border border-emerald-500/20"
      />
      <SummaryItem
        icon={Cpu}
        label="Thời gian xử lý"
        value={formatProcessingTime(response.processing_time)}
        hint="Tổng thời gian CPU"
        colorClass="text-amber-400"
        bgClass="bg-amber-500/10 border border-amber-500/20"
      />
    </div>
  );
}

export default DetectionSummary;
