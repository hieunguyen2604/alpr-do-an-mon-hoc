/**
 * Camera lifecycle: permission, device selection, stream start and release.
 *
 * Split out of the page because acquiring a camera has considerably more
 * failure modes than it first appears — denied permission, no device at all, a
 * device held by another application, an insecure origin, a camera unplugged
 * mid-session — and each one needs a different instruction. Mixing that
 * decision tree into a component that also draws overlays and tallies plates
 * makes both harder to follow.
 *
 * The hook owns the `MediaStream` and guarantees it is released: every exit
 * path, including unmount, runs through {@link stopCamera}, which stops each
 * individual track. Dropping the reference is not enough — the browser keeps
 * the device open and the camera light stays on until every track is stopped.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import type { RefObject } from 'react';

import type { CameraDevice, CameraError } from './types';

/** Lifecycle of the camera, as the UI needs to distinguish it. */
export type CameraStatus = 'idle' | 'starting' | 'streaming' | 'error';

/** Resolution to ask for. The browser may hand back the nearest it supports. */
const IDEAL_WIDTH = 1280;
const IDEAL_HEIGHT = 720;

/** What {@link useCameraStream} returns. */
export interface UseCameraStreamResult {
  /** Attach to the `<video>` element that should show the stream. */
  videoRef: RefObject<HTMLVideoElement>;
  status: CameraStatus;
  /** `true` only while frames are actually flowing. */
  isStreaming: boolean;
  /** Display-ready failure, or `null`. */
  error: CameraError | null;
  /** Every video input found. Empty until permission has been granted once. */
  devices: CameraDevice[];
  /** `deviceId` currently in use, or `null` when the camera is off. */
  activeDeviceId: string | null;
  /** Open the camera. Pass a `deviceId` to pick a specific one. */
  start: (deviceId?: string | null) => Promise<void>;
  /** Release the camera and turn its indicator light off. */
  stop: () => void;
  /** Switch to another camera, restarting the stream on it. */
  selectDevice: (deviceId: string) => Promise<void>;
  dismissError: () => void;
}

/**
 * Build the constraints for one `getUserMedia` call.
 *
 * A specific device is requested with `exact` so the browser cannot silently
 * substitute a different camera than the one the user picked from the list —
 * which would leave the dropdown showing a lie.
 *
 * @param deviceId - The camera to open, or `null` for the browser's default.
 * @returns Constraints for `getUserMedia`.
 */
function buildConstraints(deviceId?: string | null): MediaStreamConstraints {
  const video: MediaTrackConstraints = {
    width: { ideal: IDEAL_WIDTH },
    height: { ideal: IDEAL_HEIGHT },
  };

  if (deviceId) {
    video.deviceId = { exact: deviceId };
  } else {
    // A preference, not a requirement: on a laptop with only a front-facing
    // camera an `exact` facing mode would fail outright instead of falling
    // back to the one camera that exists.
    video.facingMode = 'environment';
  }

  return { video, audio: false };
}

/**
 * Translate a `getUserMedia` rejection into a message and a fix.
 *
 * Deliberately branches on `DOMException.name` rather than on the message
 * text, which is not standardised and differs between browsers. The exception
 * itself never reaches the screen (NFR-U3): the user sees Vietnamese guidance,
 * not `NotReadableError`.
 *
 * @param cause - The value rejected by the media API.
 * @returns A display-ready camera error.
 */
export function mapCameraError(cause: unknown): CameraError {
  const name = cause instanceof DOMException ? cause.name : '';

  switch (name) {
    case 'NotAllowedError':
    case 'PermissionDeniedError':
      return {
        kind: 'permission_denied',
        message: 'Trình duyệt đã chặn quyền truy cập camera.',
        hint:
          'Nhấn vào biểu tượng ổ khoá hoặc biểu tượng camera ở đầu thanh địa chỉ, ' +
          'chọn "Cho phép" cho mục Camera, sau đó tải lại trang và bấm "Bật camera" lần nữa.',
      };

    case 'NotFoundError':
    case 'DevicesNotFoundError':
      return {
        kind: 'no_device',
        message: 'Không tìm thấy camera nào trên thiết bị này.',
        hint:
          'Hãy cắm webcam vào máy, hoặc kiểm tra camera đã được bật trong cài đặt ' +
          'quyền riêng tư của hệ điều hành, rồi bấm "Bật camera" lại.',
      };

    case 'NotReadableError':
    case 'TrackStartError':
      return {
        kind: 'device_busy',
        message: 'Không mở được camera vì thiết bị đang được ứng dụng khác sử dụng.',
        hint:
          'Hãy đóng các ứng dụng đang dùng camera (Zoom, Google Meet, Microsoft Teams, ' +
          'hoặc một tab khác của trình duyệt) rồi bấm "Bật camera" lại.',
      };

    case 'OverconstrainedError':
      return {
        kind: 'constraints',
        message: 'Camera đã chọn không đáp ứng được cấu hình yêu cầu.',
        hint: 'Hãy chọn một camera khác trong danh sách thiết bị rồi thử lại.',
      };

    case 'SecurityError':
      return {
        kind: 'insecure_context',
        message: 'Trình duyệt chỉ cho phép dùng camera trên kết nối an toàn.',
        hint:
          'Hãy mở ứng dụng qua địa chỉ http://localhost hoặc qua HTTPS. ' +
          'Truy cập bằng địa chỉ IP trên HTTP sẽ bị trình duyệt chặn camera.',
      };

    default:
      return {
        kind: 'unknown',
        message: 'Không truy cập được camera.',
        hint:
          'Hãy kiểm tra camera đã được kết nối và không bị ứng dụng khác chiếm dụng, ' +
          'sau đó bấm "Bật camera" lại.',
      };
  }
}

/**
 * Manage a webcam stream and the devices available to it.
 *
 * @returns Stream state, the video ref to render, and the start/stop controls.
 */
export function useCameraStream(): UseCameraStreamResult {
  const [status, setStatus] = useState<CameraStatus>('idle');
  const [error, setError] = useState<CameraError | null>(null);
  const [devices, setDevices] = useState<CameraDevice[]>([]);
  const [activeDeviceId, setActiveDeviceId] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  /**
   * Increments on every start and stop.
   *
   * `getUserMedia` is asynchronous, so a user who clicks "Bật camera", changes
   * their mind and clicks "Tắt camera" can have the permission promise resolve
   * *after* the stop. Comparing the token captured before the await against the
   * current one tells that late arrival to release its stream instead of
   * displaying it, which is what stops a "stopped" camera from turning itself
   * back on a second later.
   */
  const startTokenRef = useRef(0);

  /**
   * List the available video inputs.
   *
   * Called again after a successful start because browsers withhold device
   * labels until permission has been granted: enumerating beforehand yields the
   * right number of cameras with empty names.
   */
  const refreshDevices = useCallback(async (): Promise<void> => {
    if (!navigator.mediaDevices?.enumerateDevices) {
      return;
    }
    try {
      const all = await navigator.mediaDevices.enumerateDevices();
      const videoInputs = all
        .filter((device) => device.kind === 'videoinput')
        .map((device, index) => ({
          deviceId: device.deviceId,
          label: device.label.trim() || `Camera ${index + 1}`,
        }));
      setDevices(videoInputs);
    } catch {
      // Enumeration is a convenience: failing to list devices must not prevent
      // the default camera from being used, so this is intentionally silent.
      setDevices([]);
    }
  }, []);

  /**
   * Release the camera.
   *
   * Every track is stopped individually. Clearing `srcObject` alone leaves the
   * device open and the indicator light on, which users reasonably read as the
   * page still watching them.
   */
  const stop = useCallback((): void => {
    startTokenRef.current += 1;

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        track.onended = null;
        track.stop();
      });
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setActiveDeviceId(null);
    setStatus((current) => (current === 'error' ? 'error' : 'idle'));
  }, []);

  /**
   * Request camera access and show the stream.
   *
   * @param deviceId - A specific camera, or `null`/omitted for the default.
   */
  const start = useCallback(
    async (deviceId?: string | null): Promise<void> => {
      // Guard the two environment failures that produce confusing exceptions
      // if left to `getUserMedia` itself.
      if (typeof window !== 'undefined' && window.isSecureContext === false) {
        setError(mapCameraError(new DOMException('', 'SecurityError')));
        setStatus('error');
        return;
      }
      if (!navigator.mediaDevices?.getUserMedia) {
        setError({
          kind: 'unsupported',
          message: 'Trình duyệt này không hỗ trợ truy cập camera.',
          hint:
            'Hãy dùng phiên bản mới của Google Chrome, Microsoft Edge hoặc Firefox ' +
            'để sử dụng chức năng nhận dạng thời gian thực.',
        });
        setStatus('error');
        return;
      }

      // Switching cameras: release the current one first, or the second
      // `getUserMedia` may fail with the device reported as busy.
      stop();

      startTokenRef.current += 1;
      const token = startTokenRef.current;

      setStatus('starting');
      setError(null);

      try {
        const stream = await navigator.mediaDevices.getUserMedia(
          buildConstraints(deviceId),
        );

        // The user stopped the camera while the permission prompt was open.
        if (token !== startTokenRef.current) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        streamRef.current = stream;

        // A track ends on its own when the camera is unplugged or taken over by
        // the operating system. Without this the page would keep capturing
        // blank frames and never say why.
        stream.getVideoTracks().forEach((track) => {
          track.onended = (): void => {
            setError({
              kind: 'disconnected',
              message: 'Camera đã ngắt kết nối.',
              hint: 'Hãy kiểm tra lại cáp kết nối hoặc thiết bị, rồi bấm "Bật camera" để tiếp tục.',
            });
            setStatus('error');
            stop();
          };
        });

        const video = videoRef.current;
        if (video) {
          video.srcObject = stream;
          // Muted playback is allowed to autostart; a rejection here means the
          // element was torn down mid-call and is not worth surfacing.
          await video.play().catch(() => undefined);
        }

        const settings = stream.getVideoTracks()[0]?.getSettings();
        setActiveDeviceId(settings?.deviceId ?? deviceId ?? null);
        setStatus('streaming');

        // Labels are only readable now that permission has been granted.
        void refreshDevices();
      } catch (cause) {
        if (token !== startTokenRef.current) {
          return;
        }
        setError(mapCameraError(cause));
        setStatus('error');
        stop();
      }
    },
    [refreshDevices, stop],
  );

  /**
   * Restart the stream on a different camera.
   *
   * @param deviceId - The camera to switch to.
   */
  const selectDevice = useCallback(
    async (deviceId: string): Promise<void> => {
      await start(deviceId);
    },
    [start],
  );

  const dismissError = useCallback((): void => {
    setError(null);
    setStatus((current) => (current === 'error' ? 'idle' : current));
  }, []);

  // Populate the device list on mount. Labels stay empty until permission is
  // granted, but the count tells us whether to show a picker at all.
  useEffect(() => {
    void refreshDevices();
  }, [refreshDevices]);

  // Keep the list current when a camera is plugged in or removed.
  useEffect(() => {
    const mediaDevices = navigator.mediaDevices;
    if (!mediaDevices?.addEventListener) {
      return undefined;
    }
    const handleChange = (): void => {
      void refreshDevices();
    };
    mediaDevices.addEventListener('devicechange', handleChange);
    return () => mediaDevices.removeEventListener('devicechange', handleChange);
  }, [refreshDevices]);

  // Release the device if the user navigates away mid-session.
  useEffect(() => stop, [stop]);

  return {
    videoRef,
    status,
    isStreaming: status === 'streaming',
    error,
    devices,
    activeDeviceId,
    start,
    stop,
    selectDevice,
    dismissError,
  };
}
