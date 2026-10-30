# Grasp Workbench

A local workbench for experimenting with interchangeable robotic grasp-prediction models. The project separates model adapters from the UI so planar (2D) and spatial (6D) grasp pipelines can be integrated behind a common interface.

## Current status

This repository is an **early scaffold**, not a ready-to-use grasp inference system.

- The Streamlit UI and model-profile registry are present.
- Model profiles describe planar depth-based and spatial grasp approaches.
- Model adapters and pretrained checkpoints are not yet fully implemented or validated.
- Live Intel RealSense D415 streaming is not yet integrated.
- No robot motion, ROS 2, or MoveIt trajectory execution is performed.

A model marked unavailable in the UI is not configured for inference. The workbench does not generate placeholder or random grasp predictions.

## Requirements

- Ubuntu or another supported Linux environment
- Python 3.11 or 3.12
- [uv](https://docs.astral.sh/uv/)

## Setup

Clone the repository and install its dependencies:

```bash
git clone https://github.com/Mohamed-faaris/grasp-workbench.git
cd grasp-workbench

uv lock
uv sync
```

Run the UI:

```bash
uv run streamlit run app.py
```

Streamlit prints the local URL (normally http://localhost:8501).

For development and tests:

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```

## Optional dependencies

Install optional extras only when needed:

```bash
# PyTorch
uv sync --extra torch

# Intel RealSense Python bindings
uv sync --extra realsense
```

The RealSense extra only installs the Python binding; it does not mean D415 capture has already been implemented in this scaffold.

## Model integration

Model profiles are defined in `configs/models.yaml`. Adapter expectations and the input/output contract are documented in [docs/ADAPTER_API.md](docs/ADAPTER_API.md).

The intended model families include:

| Model | Intended input | Output family |
|---|---|---|
| GG-CNN2 | Depth image | Planar grasp |
| GR-ConvNet | Depth image | Planar grasp |
| VGN | TSDF / voxel volume | Spatial 6-DoF grasp |
| Contact-GraspNet | Point cloud | Spatial grasp |
| GraspNet baseline | RGB-D / point cloud | Spatial grasp |

These are integration targets, not a claim that their upstream implementations or checkpoints are bundled and working. Check each upstream project's license, dependencies, checkpoint instructions, and hardware requirements before installing or running it.

## Performance and safety

- A future camera pipeline should favor dropping stale frames over building an inference backlog.
- Predictions must be validated against the camera calibration and robot coordinate frames before being used by a robot.
- This project currently does not command a robot or execute grasp trajectories.

## License

No project license has been added yet. Until one is added, do not assume the repository grants permission to redistribute or reuse its code.
