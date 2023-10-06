from typing import Protocol

from pyproj import CRS, Transformer


class Location(Protocol):
    latitude: float
    longitude: float


def create_coordinate_reference_system(location: Location) -> CRS:
    """Convert a location to a coordinate reference system."""
    crs_string = (
        "+proj=tmerc +ellps=WGS84 +datum=WGS84 +units=m +no_defs "
        f"+lon_0={location.longitude} lat_0={location.latitude} +x_0=0 +y_0=0 +k_0=1"
    )
    crs = CRS.from_string(crs_string)
    return crs


def reprojectToCrs(lat: float, lon: float, crs_from, crs_to, direction="FORWARD"):
    transformer = Transformer.from_crs(crs_from, crs_to, always_xy=True)
    pt = transformer.transform(lon, lat, direction=direction)

    return pt[0], pt[1]


class LocationWithRadius(Protocol):
    latitude: float
    longitude: float
    radius: float


def get_bounding_box(
    location_with_radius: LocationWithRadius,
) -> tuple[float, float, float, float]:
    projected_crs = create_coordinate_reference_system(location_with_radius)
    lon_plus_1_meter, lat_plus_1_meter = reprojectToCrs(
        1, 1, projected_crs, "EPSG:4326"
    )
    scale_x = lon_plus_1_meter - location_with_radius.latitude
    scale_y = lat_plus_1_meter - location_with_radius.longitude

    return (
        location_with_radius.latitude - location_with_radius.radius * scale_y,
        location_with_radius.longitude - location_with_radius.radius * scale_x,
        location_with_radius.latitude + location_with_radius.radius * scale_y,
        location_with_radius.longitude + location_with_radius.radius * scale_x,
    )
