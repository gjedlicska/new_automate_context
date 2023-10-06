from dataclasses import dataclass

import pytest
from specklepy.objects.other import Any

from utils.utils_pyproj import Reprojector


@dataclass
class Location:
    latitude: float
    longitude: float


def test_reprojector():
    def fake_transformer(
        a: float, b: float, c: bool, d: bool, e: str
    ) -> tuple[float, float]:
        return 1, 2

    re = Reprojector(fake_transformer)

    projected = re.reproject(Location(123, 123))

    assert projected == (1, 2)


def test_reprojector_rethrows_key_error_as_value_error():
    def fake_transformer(
        a: float, b: float, c: bool, d: bool, e: str
    ) -> tuple[float, float]:
        raise KeyError("fake")

    re = Reprojector(fake_transformer)
    with pytest.raises(ValueError):
        re.reproject(Location(123, 123))


def test_reprojector_from_location():
    re = Reprojector.from_location(Location(1, 1), "EPSG:4326")

    projected = re.reproject(Location(2, 2))

    assert projected == (1, 2)
