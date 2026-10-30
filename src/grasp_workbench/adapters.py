from pathlib import Path
import json
import shlex
import subprocess
import tempfile


def validate_result(result: dict, grasp_type: str) -> None:
    if not isinstance(result, dict) or not isinstance(result.get("grasps"), list):
        raise ValueError("Adapter response must contain a 'grasps' array")
    required = (("center_px", "angle_rad", "width_px", "quality")
                if grasp_type == "planar" else
                ("position_m", "quaternion_xyzw", "width_m", "score"))
    for index, grasp in enumerate(result["grasps"]):
        missing = [key for key in required if key not in grasp]
        if missing:
            raise ValueError(f"Grasp {index} missing fields: {', '.join(missing)}")


def run_adapter(spec: dict, root: Path, inputs: dict) -> dict:
    command = spec.get("command", "").strip()
    if not command:
        raise RuntimeError("No adapter command configured")
    with tempfile.TemporaryDirectory(prefix="grasp-adapter-") as temp:
        request = Path(temp) / "request.json"
        response = Path(temp) / "response.json"
        request.write_text(json.dumps({"input": inputs, "output": str(response), "options": {}}))
        argv = shlex.split(command) + ["--request", str(request)]
        proc = subprocess.run(argv, cwd=root, text=True, capture_output=True, timeout=600)
        if proc.returncode:
            raise RuntimeError(f"Adapter exit {proc.returncode}\n{proc.stdout}\n{proc.stderr}")
        if not response.exists():
            raise RuntimeError("Adapter did not write response JSON")
        return json.loads(response.read_text())
