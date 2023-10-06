import numpy as np
import requests
from attrs import define
from specklepy.objects import Base

from utils.utils_pyproj import create_coordinate_reference_system, reprojectToCrs


@define
class ProjectLocation:
    """Store project location data."""

    latitude: float
    longitude: float
    angle: float


def get_project_location(base: Base) -> ProjectLocation:
    """Get the project location from a base if its exist."""
    try:
        proj_info = base["info"]
        latitude_radians = proj_info["latitude"]
        longitute_radians = proj_info["longitude"]
        angle_radians = proj_info["locations"][0]["trueNorth"]
    except KeyError as ke:
        raise ValueError("The project info does not have the required values.", ke)

    if not all(
        [
            isinstance(latitude_radians, float),
            isinstance(longitute_radians, float),
            isinstance(angle_radians, float),
        ]
    ):
        raise ValueError("Latitude longitude and location trueNorth need to be floats.")

    try:
        latitude_degrees = np.rad2deg(latitude_radians)
        longitude_degrees = np.rad2deg(longitute_radians)
        angle_degrees = np.rad2deg(angle_radians)
    except Exception as e:
        raise ValueError("Could not convert location radians to degrees.", e)

    return ProjectLocation(latitude_degrees, longitude_degrees, angle_degrees)


def _get_building_data_from_overpass(project_location: ProjectLocation):
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""[out:json];
    (node["building"]({lat-r*scaleY},{lon-r*scaleX},{lat+r*scaleY},{lon+r*scaleX});
    way["building"]({lat-r*scaleY},{lon-r*scaleX},{lat+r*scaleY},{lon+r*scaleX});
    relation["building"]({lat-r*scaleY},{lon-r*scaleX},{lat+r*scaleY},{lon+r*scaleX});
    );out body;>;out skel qt;"""

    response = requests.get(overpass_url, params={"data": overpass_query})
    data = response.json()


def get_building_mesh_group(lat: float, lon: float, r: float):
    """Get buildings from overpass and convert them to a list of meshes."""
    # https://towardsdatascience.com/loading-data-from-openstreetmap-with-python-and-the-overpass-api-513882a27fd0

    projectedCrs = createCRS(lat, lon)
    lonPlus1, latPlus1 = reprojectToCrs(1, 1, projectedCrs, "EPSG:4326")
    scaleX = lonPlus1 - lon
    scaleY = latPlus1 - lat
    # r = RADIUS #meters

    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""[out:json];
    (node["building"]({lat-r*scaleY},{lon-r*scaleX},{lat+r*scaleY},{lon+r*scaleX});
    way["building"]({lat-r*scaleY},{lon-r*scaleX},{lat+r*scaleY},{lon+r*scaleX});
    relation["building"]({lat-r*scaleY},{lon-r*scaleX},{lat+r*scaleY},{lon+r*scaleX});
    );out body;>;out skel qt;"""

    response = requests.get(overpass_url, params={"data": overpass_query})
    data = response.json()
    features = data["elements"]

    ways = []
    tags = []

    rel_outer_ways = []
    rel_outer_ways_tags = []

    ways_part = []
    nodes = []

    for feature in features:
        # ways
        if feature["type"] == "way":
            try:
                feature["id"]
                feature["nodes"]

                try:
                    tags.append(
                        {
                            "building": feature["tags"]["building"],
                            "height": feature["tags"]["height"],
                        }
                    )
                except:
                    try:
                        tags.append(
                            {
                                "building": feature["tags"]["building"],
                                "levels": feature["tags"]["building:levels"],
                            }
                        )
                    except:
                        try:
                            tags.append(
                                {
                                    "building": feature["tags"]["building"],
                                    "layer": feature["tags"]["layer"],
                                }
                            )
                        except:
                            tags.append({"building": feature["tags"]["building"]})
                ways.append({"id": feature["id"], "nodes": feature["nodes"]})
            except:
                ways_part.append({"id": feature["id"], "nodes": feature["nodes"]})

        # relations
        elif feature["type"] == "relation":
            outer_ways = []
            try:
                outer_ways_tags = {
                    "building": feature["tags"]["building"],
                    "height": feature["tags"]["height"],
                }
            except:
                try:
                    outer_ways_tags = {
                        "building": feature["tags"]["building"],
                        "levels": feature["tags"]["building:levels"],
                    }
                except:
                    try:
                        outer_ways_tags = {
                            "building": feature["tags"]["building"],
                            "layer": feature["tags"]["layer"],
                        }
                    except:
                        outer_ways_tags = {"building": feature["tags"]["building"]}

            for n, x in enumerate(feature["members"]):
                # if several Outer ways, combine them
                if (
                    feature["members"][n]["type"] == "way"
                    and feature["members"][n]["role"] == "outer"
                ):
                    outer_ways.append({"ref": feature["members"][n]["ref"]})
            rel_outer_ways.append(outer_ways)
            rel_outer_ways_tags.append(outer_ways_tags)

        # get nodes (that don't have tags)
        elif feature["type"] == "node":
            try:
                feature["tags"]
            except:
                nodes.append(
                    {"id": feature["id"], "lat": feature["lat"], "lon": feature["lon"]}
                )

    # turn relations_OUTER into ways
    for n, x in enumerate(rel_outer_ways):
        # there will be a list of "ways" in each of rel_outer_ways
        full_node_list = []
        for m, y in enumerate(rel_outer_ways[n]):
            # find ways_parts with corresponding ID
            for k, z in enumerate(ways_part):
                if k == len(ways_part):
                    break
                if rel_outer_ways[n][m]["ref"] == ways_part[k]["id"]:
                    full_node_list += ways_part[k]["nodes"]
                    ways_part.pop(k)  # remove used ways_parts
                    k -= 1  # reset index
                    break
        ways.append({"nodes": full_node_list})
        try:
            tags.append(
                {
                    "building": rel_outer_ways_tags[n]["building"],
                    "height": rel_outer_ways_tags[n]["height"],
                }
            )
        except:
            try:
                tags.append(
                    {
                        "building": rel_outer_ways_tags[n]["building"],
                        "levels": rel_outer_ways_tags[n]["levels"],
                    }
                )
            except:
                try:
                    tags.append(
                        {
                            "building": rel_outer_ways_tags[n]["building"],
                            "layer": rel_outer_ways_tags[n]["layer"],
                        }
                    )
                except:
                    tags.append({"building": rel_outer_ways_tags[n]["building"]})

        buildingsCount = len(ways)
        # print(buildingsCount)

    # get coords of Ways
    objectGroup = []
    for i, x in enumerate(ways):  # go through each Way: 2384
        ids = ways[i]["nodes"]
        coords = []  # replace node IDs with actual coords for each Way
        height = 9
        try:
            height = (
                float(cleanString(tags[i]["levels"].split(",")[0].split(";")[0])) * 3
            )
        except:
            try:
                height = float(
                    cleanString(tags[i]["height"].split(",")[0].split(";")[0])
                )
            except:
                try:
                    if (
                        float(cleanString(tags[i]["layer"].split(",")[0].split(";")[0]))
                        < 0
                    ):
                        height = -1 * height
                except:
                    pass

        for k, y in enumerate(ids):  # go through each node of the Way
            if k == len(ids) - 1:
                continue  # ignore last
            for n, z in enumerate(nodes):  # go though all nodes
                if ids[k] == nodes[n]["id"]:
                    x, y = reprojectToCrs(
                        nodes[n]["lat"], nodes[n]["lon"], "EPSG:4326", projectedCrs
                    )
                    coords.append({"x": x, "y": y})
                    break

        obj = extrudeBuildings(coords, height)
        objectGroup.append(obj)
        coords = None
        height = None
    return objectGroup
