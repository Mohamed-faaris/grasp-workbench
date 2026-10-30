# Grasp Workbench — 2D + 6D model UI

A unified local interface for comparing planar 2D grasp detectors and spatial 6-DoF grasp generators. The UI host uses `uv`; upstream model implementations run in isolated environments because their Python, CUDA, TensorFlow and custom-operator requirements conflict.

> **Current status:** UI, registry and adapter protocol scaffold. Upstream model inference adapters are not yet implemented. Models remain `NOT CONFIGURED` until a compatible adapter, environment and checkpoint are installed. The UI does not fabricate predictions.

## Model profiles

| Model | Grasp type | Input |
|---|---|---|
| GG-CNN2 | Planar | Depth |
| GR-ConvNet | Planar | Depth |
| VGN | 6-DoF | TSDF / voxel volume |
| Contact-GraspNet | 6-DoF | Point cloud |
| GraspNet baseline | 6-DoF | RGB-D + intrinsics |

## Quick start (Ubuntu)

```bash
sudo apt update
sudo apt install -y git python3.11 python3.11-venv libgl1 libglib2.0-0
curl -LsSf https://astral.sh/uv/install.sh | sh

git clone https://github.com/Mohamed-faaris/grasp-workbench.git
cd grasp-workbench
uv sync
uv run streamlit run app.py
```

Open the local URL printed by Streamlit (normally http://localhost:8501).

## Download upstream repositories

```bash
bash scripts/clone_models.sh
```

Or individually:

```bash
git clone https://github.com/skumra/robotic-grasping.git external/robotic-grasping
git clone https://github.com/ethz-asl/vgn.git external/vgn
git clone https://github.com/NVlabs/contact_graspnet.git external/contact_graspnet
git clone https://github.com/graspnet/graspnet-baseline.git external/graspnet-baseline
```

## Weights and model assets

Install gdown:

```bash
uv tool install gdown
```

### VGN data archive

```bash
mkdir -p external/vgn/data
gdown --fuzzy "https://drive.google.com/file/d/1MysYHve3ooWiLq12b58Nm8FWiFBMH-bJ/view?usp=sharing" -O /tmp/vgn-data.zip
unzip -q /tmp/vgn-data.zip -d external/vgn/data
```

Check for `external/vgn/data/models/vgn_conv.pth`; adjust if the archive contains an extra nested directory.

### Contact-GraspNet checkpoints

```bash
mkdir -p external/contact_graspnet/checkpoints
gdown --folder "https://drive.google.com/drive/folders/1tBHKf60K8DLM5arm-Chyf7jxkzOr5zGl?usp=sharing" -O external/contact_graspnet/checkpoints
```

### GraspNet baseline RealSense checkpoint

```bash
mkdir -p external/graspnet-baseline
gdown --fuzzy "https://drive.google.com/file/d/1hd0G8LN6tRpi4742XOTEisbTXNZ-1jmk/view?usp=sharing" -O external/graspnet-baseline/checkpoint-rs.tar
```

### GR-ConvNet and GG-CNN2

Inspect available GR-ConvNet model files after cloning:

```bash
find external/robotic-grasping/trained-models -maxdepth 3 -type f -print
```

GG-CNN2 checkpoint formats vary by implementation and training dataset. Supply a checkpoint compatible with the chosen implementation. Do not assume unrelated `.pt` or `.pth` files are interchangeable.

## Model environments

Do not install every upstream model's requirements into this UI environment.

### GR-ConvNet

```bash
cd external/robotic-grasping
uv venv --python 3.10 .venv
uv pip install --python .venv/bin/python numpy opencv-python matplotlib scikit-image imageio pillow torch torchvision torchsummary tensorboardX
cd ../..
```

Verify the supported Python/PyTorch versions against the upstream repository before running inference.

### VGN

The upstream project targets an older Python / Ubuntu stack. Its dependencies may require a compatible system toolchain:

```bash
cd external/vgn
uv venv --python 3.8 .venv
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python -e .
cd ../..
```

### Contact-GraspNet

The upstream implementation documents an older TensorFlow/CUDA stack and compiled point-cloud operators. Follow its own environment instructions and compile its TensorFlow point-cloud ops:

```bash
cd external/contact_graspnet
bash compile_pointnet_tfops.sh
cd ../..
```

This is not a plain `uv sync` install. Match TensorFlow, CUDA and compiler versions to the upstream instructions.

### GraspNet baseline

The baseline requires matching PyTorch/CUDA and custom CUDA extensions:

```bash
cd external/graspnet-baseline
uv venv --python 3.8 .venv
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python open3d
uv pip install --python .venv/bin/python ./graspnetAPI
cd pointnet2 && ../.venv/bin/python setup.py install
cd ../knn && ../.venv/bin/python setup.py install
cd ../..
```

## Adapter contract

Every model backend is launched as a separate process. It accepts a JSON request file via `--request PATH` and writes its JSON result to the request's `output` path. See [docs/ADAPTER_API.md](docs/ADAPTER_API.md).

Configure a model in `configs/models.yaml`:

```yaml
models:
  my-model:
    enabled: true
    command: "external/my-model/.venv/bin/python external/my-model_adapter.py"
    checkpoint: "external/my-model/checkpoints/model.pth"
```

An adapter must translate the upstream model's native input/output to the shared API. The UI validates response fields and surfaces adapter failures. The included profiles remain disabled until their adapters are implemented and tested.

## D415 camera

The initial UI accepts uploaded RGB, depth and point-cloud files. RealSense support can be installed with:

```bash
uv sync --extra realsense
```

Live capture and model-specific preprocessing adapters are future integration work.

## Safety and coordinate frames

- 2D planar grasps are not 6-DoF poses.
- 6D predictions are normally in the camera frame, not the CR5A base frame.
- Camera-to-base conversion requires a validated hand-eye transform.
- Check grasp width against the PGEA-100-40-W limits and finger geometry.
- This project does not connect to ROS controllers, MoveIt execution or robot motion.
- Never execute grasps from unvalidated weights or unverified adapter outputs.

## Upstream projects

- [GR-ConvNet](https://github.com/skumra/robotic-grasping)
- [VGN](https://github.com/ethz-asl/vgn)
- [Contact-GraspNet](https://github.com/NVlabs/contact_graspnet)
- [GraspNet baseline](https://github.com/graspnet/graspnet-baseline)
