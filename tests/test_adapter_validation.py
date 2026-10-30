import pytest
from grasp_workbench.adapters import validate_result


def test_planar_schema():
    validate_result({"grasps": [{"center_px": [1, 2], "angle_rad": 0.1,
                                 "width_px": 20, "quality": 0.8}]}, "planar")


def test_spatial_schema():
    validate_result({"grasps": [{"position_m": [0, 0, 1],
                                 "quaternion_xyzw": [0, 0, 0, 1],
                                 "width_m": 0.04, "score": 0.7}]}, "spatial")


def test_invalid_schema_rejected():
    with pytest.raises(ValueError):
        validate_result({"grasps": [{"center_px": [1, 2]}]}, "planar")
