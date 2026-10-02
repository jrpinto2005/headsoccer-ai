import pytest

from hsai.emulator._proto import emulator_controller_pb2 as pb
from hsai.emulator.coords import TouchMapper


@pytest.fixture
def landscape() -> TouchMapper:
    return TouchMapper(1080, 1920, pb.Rotation.LANDSCAPE)


def test_portrait_is_identity() -> None:
    mapper = TouchMapper(1080, 1920, pb.Rotation.PORTRAIT)
    assert mapper.frame_size == (1080, 1920)
    assert mapper.to_touch(100, 200) == (100, 200)


def test_landscape_frame_size(landscape: TouchMapper) -> None:
    assert landscape.frame_size == (1920, 1080)


def test_landscape_matches_measured_points(landscape: TouchMapper) -> None:
    # Measured with the pointer-location overlay: touch (840, 960) drew at frame (960, 240),
    # and frame (1616, 172) (the promo banner's close button) was hit by touch (908, 1616).
    assert landscape.to_touch(960, 240) == (839, 960)
    assert landscape.to_touch(1616, 172) == (907, 1616)


def test_landscape_corners_stay_on_panel(landscape: TouchMapper) -> None:
    assert landscape.to_touch(0, 0) == (1079, 0)
    assert landscape.to_touch(1919, 1079) == (0, 1919)


def test_normalized(landscape: TouchMapper) -> None:
    assert landscape.to_touch_normalized(0.5, 0.5) == (539, 960)


def test_out_of_frame_is_rejected(landscape: TouchMapper) -> None:
    with pytest.raises(ValueError, match="outside"):
        landscape.to_touch(1920, 10)


def test_unverified_rotation_is_rejected() -> None:
    with pytest.raises(NotImplementedError):
        TouchMapper(1080, 1920, pb.Rotation.REVERSE_LANDSCAPE)
