from pathlib import Path
import tempfile
import streamlit as st
from grasp_workbench.registry import load_registry, model_status
from grasp_workbench.adapters import run_adapter, validate_result

ROOT = Path(__file__).parent.resolve()
st.set_page_config(page_title="Grasp Workbench", layout="wide")
st.title("Grasp Workbench")
st.caption("Unified 2D and 6D grasp model interface · RGB-D inputs · perception only")

registry = load_registry(ROOT / "configs/models.yaml")
labels = {spec["label"]: model_id for model_id, spec in registry.items()}
with st.sidebar:
    st.header("Model")
    selected = st.selectbox("Choose model", list(labels))
    model_id = labels[selected]
    spec = registry[model_id]
    status = model_status(spec, ROOT)
    st.write(f"**Type:** {spec['grasp_type']}")
    st.write(f"**Status:** {status}")
    st.caption(spec["description"])

col1, col2 = st.columns(2)
with col1:
    st.subheader("Input")
    rgb = st.file_uploader("RGB image", type=["png", "jpg", "jpeg"])
    depth = st.file_uploader("Depth image", type=["npy", "png", "tif", "tiff"])
    cloud = st.file_uploader("Point cloud (.ply)", type=["ply"])
    st.subheader("Camera intrinsics")
    fx = st.number_input("fx", min_value=0.0, value=600.0)
    fy = st.number_input("fy", min_value=0.0, value=600.0)
    cx = st.number_input("cx", min_value=0.0, value=320.0)
    cy = st.number_input("cy", min_value=0.0, value=240.0)
    run = st.button("Run selected model", type="primary", disabled=status != "READY")

with col2:
    st.subheader("Predictions")
    st.info("A model must have a configured adapter, compatible environment and checkpoint before inference is enabled.")

if run:
    if not any((depth, cloud)):
        st.error("Upload a depth image or point cloud.")
        st.stop()
    with tempfile.TemporaryDirectory(prefix="grasp-workbench-") as tmpdir:
        tmp = Path(tmpdir)
        inputs = {}
        for key, upload in (("rgb", rgb), ("depth", depth), ("point_cloud", cloud)):
            if upload:
                path = tmp / upload.name
                path.write_bytes(upload.getvalue())
                inputs[key] = str(path)
        inputs["intrinsics"] = {"fx": fx, "fy": fy, "cx": cx, "cy": cy}
        try:
            result = run_adapter(spec, ROOT, inputs)
            validate_result(result, spec["grasp_type"])
            st.success(f"Inference completed: {len(result['grasps'])} grasp(s)")
            st.json(result)
        except Exception as exc:
            st.exception(exc)

st.divider()
st.subheader("Model readiness")
cols = st.columns(len(registry))
for col, (mid, mspec) in zip(cols, registry.items()):
    with col:
        st.markdown(f"**{mspec['label']}**")
        st.caption(mspec["grasp_type"])
        st.write(model_status(mspec, ROOT))
