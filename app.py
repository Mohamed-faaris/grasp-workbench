from pathlib import Path
import json
import tempfile
import time

import numpy as np
import streamlit as st
from PIL import Image

from grasp_workbench.adapters import run_adapter, validate_result
from grasp_workbench.camera import RealSenseCamera, list_devices
from grasp_workbench.registry import load_registry, model_status

ROOT = Path(__file__).parent.resolve()
st.set_page_config(page_title="Grasp Workbench", layout="wide")
st.title("Grasp Workbench")
st.caption("Intel RealSense SDK · D415 RGB-D capture · repeatable single-frame inference")

if "camera" not in st.session_state:
    st.session_state.camera = RealSenseCamera()
if "frozen_frame" not in st.session_state:
    st.session_state.frozen_frame = None

camera: RealSenseCamera = st.session_state.camera
registry = load_registry(ROOT / "configs/models.yaml")
labels = {spec["label"]: model_id for model_id, spec in registry.items()}

with st.sidebar:
    st.header("RealSense camera")
    try:
        devices = list_devices()
        device_labels = {
            f"{item['name']} · {item['serial']}": item["serial"] for item in devices
        }
    except RuntimeError as exc:
        devices = []
        device_labels = {}
        st.error(str(exc))

    selected_device = st.selectbox(
        "Device", list(device_labels), disabled=not device_labels
    ) if device_labels else None
    resolution = st.selectbox("Resolution", ["640 × 480", "848 × 480", "1280 × 720"])
    fps = st.select_slider("FPS", options=[15, 30, 60], value=30)
    width, height = (int(value) for value in resolution.split(" × "))

    start_col, stop_col = st.columns(2)
    if start_col.button("Start camera", type="primary", disabled=not devices):
        try:
            camera.width, camera.height, camera.fps = width, height, fps
            camera.start(device_labels[selected_device])
            st.session_state.frozen_frame = None
            st.rerun()
        except Exception as exc:
            st.error(f"Could not start RealSense: {exc}")
    if stop_col.button("Stop camera"):
        camera.stop()
        st.rerun()

    st.divider()
    st.header("Model")
    selected_model = st.selectbox("Choose model", list(labels))
    model_id = labels[selected_model]
    spec = registry[model_id]
    status = model_status(spec, ROOT)
    st.write(f"**Type:** {spec['grasp_type']}")
    st.write(f"**Status:** {status}")
    st.caption(spec["description"])

st.subheader("Live D415 stream")
if camera.status == "RUNNING":
    st.success(f"Streaming · {camera.serial or 'default device'}")
else:
    st.info(f"Camera: {camera.status}")

@st.fragment(run_every="200ms")
def live_preview():
    frame = camera.latest_frame()
    if frame is None:
        st.info("Start the RealSense camera to see the live RGB-D stream.")
        return
    preview, details = st.columns([3, 1])
    with preview:
        st.image(frame["color_rgb"], channels="RGB", caption="Live RGB")
    with details:
        st.metric("Frames received", camera.frame_number)
        st.metric("Depth resolution", f"{frame['depth_m'].shape[1]} × {frame['depth_m'].shape[0]}")
        valid = frame["depth_m"][frame["depth_m"] > 0]
        if valid.size:
            st.metric("Valid depth", f"{valid.size / frame['depth_m'].size:.0%}")
            st.caption(f"Depth range: {valid.min():.2f}–{valid.max():.2f} m")

live_preview()

capture_col, clear_col, _ = st.columns([1, 1, 4])
if capture_col.button("Capture one frame", type="primary", disabled=camera.status != "RUNNING"):
    captured = camera.latest_frame()
    if captured is None:
        st.error("No frame received yet. Wait for the camera stream.")
    else:
        st.session_state.frozen_frame = captured
        ts_dir = ROOT / "data" / "timestamps" / str(int(captured["timestamp_ms"]))
        ts_dir.mkdir(parents=True, exist_ok=True)
        Image.fromarray(captured["color_rgb"]).save(ts_dir / "rgb.png")
        np.save(ts_dir / "depth_m.npy", captured["depth_m"])
        (ts_dir / "intrinsics.json").write_text(json.dumps(captured["intrinsics"]))
        (ts_dir / "timestamp_ms.txt").write_text(str(captured["timestamp_ms"]))
        st.success(f"Captured frame #{camera.frame_number}. Saved to {ts_dir}.")
if clear_col.button("Clear frame"):
    st.session_state.frozen_frame = None

st.divider()
st.caption("Saved captures")
saved_root = ROOT / "data" / "timestamps"
saved_dirs = sorted(
    [d for d in saved_root.iterdir() if d.is_dir()],
    key=lambda d: d.name,
    reverse=True,
)
saved_labels = [d.name for d in saved_dirs]
if saved_labels:
    load_sel = st.selectbox("Load saved capture", ["<none>"] + saved_labels)
    if load_sel != "<none>" and st.button("Load selected capture"):
        ts_dir = saved_root / load_sel
        st.session_state.frozen_frame = {
            "color_rgb": np.array(Image.open(ts_dir / "rgb.png")),
            "depth_m": np.load(ts_dir / "depth_m.npy"),
            "intrinsics": json.loads((ts_dir / "intrinsics.json").read_text()),
            "timestamp_ms": float((ts_dir / "timestamp_ms.txt").read_text()),
        }

frozen = st.session_state.frozen_frame
if frozen is not None:
    st.divider()
    st.subheader("Frozen input frame")
    left, right, meta = st.columns([2, 2, 1])
    with left:
        st.image(frozen["color_rgb"], caption="Captured RGB frame", channels="RGB")
    with right:
        depth = frozen["depth_m"]
        valid = depth > 0
        if np.any(valid):
            near, far = np.percentile(depth[valid], [2, 98])
            normalized = np.zeros(depth.shape, dtype=np.uint8)
            if far > near:
                normalized[valid] = np.clip(
                    (depth[valid] - near) * 255 / (far - near), 0, 255
                ).astype(np.uint8)
            st.image(normalized, caption="Aligned depth (visualized)", clamp=True)
        else:
            st.warning("Captured depth frame contains no valid pixels.")
    with meta:
        st.write("**Intrinsics**")
        st.json(frozen["intrinsics"])
        st.write(f"**Camera timestamp:** {frozen['timestamp_ms']:.1f} ms")
        st.write(f"**Depth dtype:** {frozen['depth_m'].dtype}")
        st.write(f"**Depth units:** metres")

    st.divider()
    st.subheader("Reprocess this same frame")
    st.caption(
        "The camera can keep streaming, but inference reads only the frozen RGB-D arrays below. "
        "No new frame is captured during these passes."
    )
    passes = st.number_input("Number of repeated inference passes", min_value=1, max_value=20, value=3)
    run_disabled = status != "READY"
    if run_disabled:
        st.warning(
            f"{selected_model} is {status.lower()}. Configure its adapter and checkpoint "
            "before inference can run. No placeholder predictions are generated."
        )
    if st.button("Run model repeatedly on frozen frame", type="primary", disabled=run_disabled):
        with tempfile.TemporaryDirectory(prefix="grasp-workbench-frame-") as tmp:
            tmp_path = Path(tmp)
            rgb_path = tmp_path / "rgb.png"
            depth_path = tmp_path / "depth_m.npy"
            Image.fromarray(frozen["color_rgb"]).save(rgb_path)
            np.save(depth_path, frozen["depth_m"])
            inputs = {
                "rgb": str(rgb_path),
                "depth": str(depth_path),
                "intrinsics": frozen["intrinsics"],
            }
            results = []
            durations = []
            progress = st.progress(0, text="Starting inference passes")
            for index in range(int(passes)):
                started = time.perf_counter()
                try:
                    result = run_adapter(spec, ROOT, inputs)
                    validate_result(result, spec["grasp_type"])
                except Exception as exc:
                    st.error(f"Pass {index + 1} failed: {exc}")
                    break
                durations.append(time.perf_counter() - started)
                results.append(result)
                progress.progress((index + 1) / int(passes), text=f"Completed pass {index + 1}/{int(passes)}")
            if results:
                st.success(f"Completed {len(results)} pass(es) on the same captured frame.")
                st.metric("Mean inference time", f"{np.mean(durations) * 1000:.1f} ms")
                st.metric("Grasps in final pass", len(results[-1]["grasps"]))
                annotated = np.array(frozen["color_rgb"]).copy()
                try:
                    import cv2
                    for g in results[-1]["grasps"]:
                        cx, cy = int(g["center_px"][0]), int(g["center_px"][1])
                        ang = float(g["angle_rad"])
                        length = int(g.get("width_px", 40) * 2)
                        dx = int(np.cos(ang) * length / 2)
                        dy = int(np.sin(ang) * length / 2)
                        cv2.circle(annotated, (cx, cy), 4, (0, 255, 0), -1)
                        cv2.line(annotated, (cx - dx, cy - dy), (cx + dx, cy + dy), (255, 0, 0), 2)
                    st.image(annotated, caption="Annotated grasps", channels="RGB")
                except Exception:
                    pass
                st.json(results[-1])
                with st.expander("All pass outputs"):
                    for index, (result, duration) in enumerate(zip(results, durations), start=1):
                        st.markdown(f"**Pass {index} · {duration * 1000:.1f} ms**")
                        st.json(result)
else:
    st.info("Capture a frame from the live D415 stream to freeze it for repeated inference.")

st.divider()
st.subheader("Model readiness")
cols = st.columns(len(registry))
for col, (mid, model_spec) in zip(cols, registry.items()):
    with col:
        st.markdown(f"**{model_spec['label']}**")
        st.caption(model_spec["grasp_type"])
        st.write(model_status(model_spec, ROOT))
