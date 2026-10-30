# Model adapter API

Each model runs in a separate process so incompatible Python, TensorFlow, PyTorch and CUDA dependencies remain isolated.

Invocation:

```bash
python adapter.py --request /path/to/request.json
```

Request JSON:

```json
{
  "input": {
    "depth": "/absolute/path/depth.npy",
    "rgb": "/absolute/path/rgb.png",
    "intrinsics": {"fx": 600, "fy": 600, "cx": 320, "cy": 240},
    "point_cloud": "/absolute/path/scene.ply"
  },
  "output": "/absolute/path/result.json",
  "options": {}
}
```

Planar grasp schema:

```json
{"model":"grconvnet","grasp_type":"planar","grasps":[{"center_px":[150,140],"angle_rad":0.2,"width_px":44,"quality":0.9}]}
```

Spatial grasp schema:

```json
{"model":"vgn","grasp_type":"spatial","grasps":[{"position_m":[0.1,0,0.5],"quaternion_xyzw":[0,0,0,1],"width_m":0.04,"score":0.8}]}
```

Spatial poses default to camera frame. The workbench does not transform poses to the robot base or execute motion.
