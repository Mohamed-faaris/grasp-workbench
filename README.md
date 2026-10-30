# Grasp Workbench

A local workbench for Intel RealSense RGB-D capture and repeatable grasp-model inference.

## What it does

- Captures aligned RGB and depth frames directly through the Intel RealSense SDK (`pyrealsense2`); no photo upload is required.
- Keeps a latest-frame-only camera buffer, dropping stale frames rather than building a queue.
- Lets you freeze one captured RGB-D frame.
- Runs a configured model repeatedly against that exact frozen frame. The camera may continue streaming, but inference inputs remain unchanged until you capture another frame.
- Supports planar (2D) and spatial (6D) model adapter profiles.

## Requirements

- Ubuntu or another supported Linux environment
- Python 3.11 or 3.12
- Intel RealSense D415 (or a compatible RealSense device)
- Intel RealSense SDK / librealsense installed and the camera accessible to your user
- [uv](https://docs.astral.sh/uv/)

## Install

```bash
git clone https://github.com/Mohamed-faaris/grasp-workbench.git
cd grasp-workbench
uv sync --extra realsense
uv run streamlit run app.py
```

If the SDK cannot find the camera, install/configure librealsense and its udev rules for your Ubuntu release, reconnect the camera, and verify it with `rs-enumerate-devices`.

## Workflow

1. Select the D415 device, resolution, and FPS in the sidebar.
2. Start the camera and inspect the live RGB preview and aligned depth status.
3. Click **Capture one frame**. The RGB image, depth array (metres), and camera intrinsics are frozen together.
4. Select a model and choose the number of repeated passes.
5. Click **Run model repeatedly on frozen frame**. Every pass receives the same RGB/depth files and intrinsics; no camera frame is substituted mid-run.

## Model integration status

The UI contains model profiles, but model-specific adapters/checkpoints still need to be installed and configured before predictions can run.

| Model | Input | Output |
|---|---|---|
| GG-CNN2 | Depth image | Planar grasp |
| GR-ConvNet | Depth image | Planar grasp |
| VGN | TSDF / voxel volume | Spatial 6-DoF grasp |
| Contact-GraspNet | Point cloud | Spatial grasp |
| GraspNet baseline | RGB-D / point cloud | Spatial grasp |

The camera capture path is implemented; this does **not** mean the above model inference backends are already implemented or validated. Models marked unavailable are disabled. No random or placeholder grasp outputs are shown.

Adapter request/response format: [docs/ADAPTER_API.md](docs/ADAPTER_API.md).

## Notes

- The SDK capture thread stores only the newest frame to prevent latency from accumulating.
- Depth is aligned to the color stream and converted from device units to metres.
- This project does not publish ROS topics, transform poses into the robot base frame, or execute robot motion.
