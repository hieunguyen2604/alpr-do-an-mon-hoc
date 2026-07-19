/**
 * Camera on/off, device picker and capture-rate selector.
 */

import { Camera, CameraOff, RefreshCw } from 'lucide-react';

import { FRAME_INTERVAL_OPTIONS } from './constants';
import type { CameraDevice } from './types';

/** Props of {@link CameraControls}. */
export interface CameraControlsProps {
  isStreaming: boolean;
  isStarting: boolean;
  devices: readonly CameraDevice[];
  activeDeviceId: string | null;
  intervalMs: number;
  onStart: () => void;
  onStop: () => void;
  onSelectDevice: (deviceId: string) => void;
  onIntervalChange: (intervalMs: number) => void;
}

/**
 * Render the camera controls.
 *
 * @param props - Stream state, device list and the change handlers.
 * @returns The control bar.
 */
export function CameraControls({
  isStreaming,
  isStarting,
  devices,
  activeDeviceId,
  intervalMs,
  onStart,
  onStop,
  onSelectDevice,
  onIntervalChange,
}: CameraControlsProps): JSX.Element {
  return (
    <div className="flex flex-wrap items-end gap-3">
      {/* Only worth showing when there is an actual choice to make. */}
      {devices.length > 1 && (
        <div className="min-w-[12rem] flex-1">
          <label className="label text-xs" htmlFor="webcam-device">
            Thiết bị camera
          </label>
          <select
            id="webcam-device"
            className="input"
            value={activeDeviceId ?? ''}
            onChange={(event) => onSelectDevice(event.target.value)}
            disabled={isStarting}
          >
            {activeDeviceId === null && (
              <option value="">Camera mặc định</option>
            )}
            {devices.map((device) => (
              <option key={device.deviceId} value={device.deviceId}>
                {device.label}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="min-w-[12rem] flex-1">
        <label className="label text-xs" htmlFor="webcam-interval">
          Chu kỳ gửi khung hình
        </label>
        <select
          id="webcam-interval"
          className="input"
          value={intervalMs}
          onChange={(event) => onIntervalChange(Number(event.target.value))}
        >
          {FRAME_INTERVAL_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-2">
        {isStreaming ? (
          <button type="button" onClick={onStop} className="btn-danger">
            <CameraOff size={15} aria-hidden="true" />
            Tắt camera
          </button>
        ) : (
          <button
            type="button"
            onClick={onStart}
            disabled={isStarting}
            className="btn-primary"
          >
            {isStarting ? (
              <RefreshCw size={15} className="animate-spin" aria-hidden="true" />
            ) : (
              <Camera size={15} aria-hidden="true" />
            )}
            {isStarting ? 'Đang khởi động…' : 'Bật camera'}
          </button>
        )}
      </div>
    </div>
  );
}

export default CameraControls;
