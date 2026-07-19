/**
 * Tunable values of the realtime view.
 *
 * In their own module rather than beside the control component so that file
 * exports components only — a mixed module defeats Vite's fast refresh, which
 * would mean a full page reload (and a released camera) on every edit.
 */

/** One capture-rate choice offered in the dropdown. */
export interface FrameIntervalOption {
  /** Delay between capture attempts, in milliseconds. */
  value: number;
  /** Vietnamese label. */
  label: string;
}

/**
 * Capture intervals the user can choose between.
 *
 * These are *attempt* rates, not guaranteed throughput. The loop sends at most
 * one frame at a time, so picking 400 ms on a machine that needs 600 ms per
 * frame does not produce 2.5 FPS — it produces the same rate as before plus a
 * larger count of skipped frames.
 */
export const FRAME_INTERVAL_OPTIONS: readonly FrameIntervalOption[] = [
  { value: 400, label: 'Nhanh — 400 ms/khung' },
  { value: 700, label: 'Cân bằng — 700 ms/khung' },
  { value: 1000, label: 'Tiết kiệm — 1 giây/khung' },
  { value: 2000, label: 'Chậm — 2 giây/khung' },
];

/**
 * Interval used until the user chooses otherwise.
 *
 * 700 ms sits just above the ~300-400 ms the CPU pipeline needs per frame, so
 * the loop usually finds its slot free. Going faster does not raise throughput;
 * the extra frames are dropped, and only the browser's capture and JPEG
 * encoding work is wasted.
 */
export const DEFAULT_FRAME_INTERVAL_MS = 700;
