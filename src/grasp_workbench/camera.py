"""Intel RealSense SDK capture with a latest-frame-only worker.

The capture thread intentionally overwrites its previous frame. Consumers always
receive the newest frame instead of accumulating a queue of stale camera frames.
"""
from __future__ import annotations

import threading
import time
from typing import Any

import numpy as np


def list_devices() -> list[dict[str, str]]:
    """Return connected RealSense devices without starting a stream."""
    try:
        import pyrealsense2 as rs
    except ImportError as exc:
        raise RuntimeError(
            "pyrealsense2 is not installed. Install with: uv sync --extra realsense"
        ) from exc

    context = rs.context()
    devices = []
    for device in context.query_devices():
        devices.append({
            "name": device.get_info(rs.camera_info.name),
            "serial": device.get_info(rs.camera_info.serial_number),
        })
    return devices


class RealSenseCamera:
    """Background D415-compatible RGB-D capture using librealsense/pyrealsense2."""

    def __init__(self, width: int = 640, height: int = 480, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self._lock = threading.Lock()
        self._latest: dict[str, Any] | None = None
        self._pipeline = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._status = "STOPPED"
        self._error: str | None = None
        self._frame_number = 0
        self._serial: str | None = None

    @property
    def status(self) -> str:
        return self._status

    @property
    def error(self) -> str | None:
        return self._error

    @property
    def serial(self) -> str | None:
        return self._serial

    @property
    def frame_number(self) -> int:
        return self._frame_number

    def start(self, serial: str | None = None) -> None:
        if self._thread and self._thread.is_alive():
            return
        try:
            import pyrealsense2 as rs
        except ImportError as exc:
            raise RuntimeError(
                "pyrealsense2 is missing. Run: uv sync --extra realsense"
            ) from exc

        pipeline = rs.pipeline()
        config = rs.config()
        if serial:
            config.enable_device(serial)
        config.enable_stream(
            rs.stream.color, self.width, self.height, rs.format.bgr8, self.fps
        )
        config.enable_stream(
            rs.stream.depth, self.width, self.height, rs.format.z16, self.fps
        )

        profile = pipeline.start(config)
        depth_sensor = profile.get_device().first_depth_sensor()
        depth_scale = float(depth_sensor.get_depth_scale())
        align = rs.align(rs.stream.color)

        self._pipeline = pipeline
        self._serial = serial
        self._stop.clear()
        self._error = None
        self._status = "RUNNING"
        self._thread = threading.Thread(
            target=self._capture_loop,
            args=(pipeline, align, depth_scale, rs),
            name="realsense-latest-frame",
            daemon=True,
        )
        self._thread.start()

    def _capture_loop(self, pipeline, align, depth_scale: float, rs) -> None:
        try:
            while not self._stop.is_set():
                frames = pipeline.wait_for_frames(timeout_ms=1000)
                aligned = align.process(frames)
                color_frame = aligned.get_color_frame()
                depth_frame = aligned.get_depth_frame()
                if not color_frame or not depth_frame:
                    continue

                color_bgr = np.asanyarray(color_frame.get_data()).copy()
                color_rgb = color_bgr[:, :, ::-1].copy()
                depth_m = (
                    np.asanyarray(depth_frame.get_data()).astype(np.float32)
                    * depth_scale
                )
                intr = color_frame.profile.as_video_stream_profile().intrinsics
                frame = {
                    "color_rgb": color_rgb,
                    "depth_m": depth_m,
                    "intrinsics": {
                        "fx": float(intr.fx),
                        "fy": float(intr.fy),
                        "cx": float(intr.ppx),
                        "cy": float(intr.ppy),
                        "width": int(intr.width),
                        "height": int(intr.height),
                    },
                    "timestamp_ms": float(color_frame.get_timestamp()),
                    "captured_at": time.time(),
                }
                with self._lock:
                    self._latest = frame
                    self._frame_number += 1
        except Exception as exc:
            if not self._stop.is_set():
                self._error = str(exc)
                self._status = "ERROR"
        finally:
            if self._stop.is_set():
                self._status = "STOPPED"

    def latest_frame(self) -> dict[str, Any] | None:
        with self._lock:
            if self._latest is None:
                return None
            return {
                **self._latest,
                "color_rgb": self._latest["color_rgb"].copy(),
                "depth_m": self._latest["depth_m"].copy(),
                "intrinsics": dict(self._latest["intrinsics"]),
            }

    def stop(self) -> None:
        self._stop.set()
        if self._pipeline is not None:
            try:
                self._pipeline.stop()
            except Exception:
                pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._pipeline = None
        self._status = "STOPPED"

    def __del__(self):
        self.stop()
