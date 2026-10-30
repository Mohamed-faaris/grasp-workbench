from pathlib import Path
import yaml


def load_registry(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data.get("models", {})


def model_status(spec: dict, root: Path) -> str:
    if not spec.get("enabled") or not spec.get("command", "").strip():
        return "NOT CONFIGURED"
    checkpoint = root / spec.get("checkpoint", "")
    if not checkpoint.exists():
        return "CHECKPOINT MISSING"
    return "READY"
