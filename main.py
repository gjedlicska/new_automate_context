"""This module contains the business logic of the function.

use the automation_context module to wrap your function in an Autamate context helper
"""
# from flatten import flatten_base
import numpy as np
from attrs import define
from pydantic import Field
from speckle_automate import (
    AutomateBase,
    AutomationContext,
    execute_automate_function,
)
from specklepy.objects import Base
from specklepy.objects.other import Collection

from utils.utils_osm import getBuildings, getRoads
from utils.utils_other import RESULT_BRANCH


class FunctionInputs(AutomateBase):
    """These are function author defined values.

    Automate will make sure to supply them matching the types specified here.
    Please use the pydantic model schema to define your inputs:
    https://docs.pydantic.dev/latest/usage/models/
    """

    radius_in_meters: float = Field(
        title="Radius in meters",
        description=(
            "Radius from the Model location," " derived from Revit model lat, lon."
        ),
    )


def automate_function(
    automate_context: AutomationContext,
    function_inputs: FunctionInputs,
) -> None:
    """This is an example Speckle Automate function.

    Args:
        automate_context: A context helper object, that carries relevant information
            about the runtime context of this function.
            It gives access to the Speckle project data, that triggered this run.
            It also has conveniece methods attach result data to the Speckle model.
        function_inputs: An instance object matching the defined schema.
    """
    try:
        # automate_context.version_source_application()
        base = automate_context.receive_version()

        project_id = automate_context.automation_run_data.project_id

        project_location = get_project_location(base)

        blds = getBuildings(
            project_location.latitude,
            project_location.longitude,
            function_inputs.radius_in_meters,
        )
        bases = [Base(units="m", displayValue=[b]) for b in blds]
        bldObj = Collection(
            elements=bases, units="m", name="Context", collectionType="BuildingsLayer"
        )

        roads, meshes, analysisMeshes = getRoads(
            lat, lon, function_inputs.radius_in_meters
        )
        roadObj = Collection(
            elements=roads, units="m", name="Context", collectionType="RoadsLayer"
        )
        roadMeshObj = Collection(
            elements=meshes, units="m", name="Context", collectionType="RoadMeshesLayer"
        )

        commitObj = Collection(
            elements=[], units="m", name="Context", collectionType="BuildingsLayer"
        )

        # add objects to new Collection
        commitObj.elements.append(bldObj)
        commitObj.elements.append(roadObj)
        commitObj.elements.append(roadMeshObj)

        # create branch if needed
        existing_branch = automate_context.speckle_client.branch.get(
            project_id, RESULT_BRANCH, 1
        )
        if existing_branch is None:
            br_id = automate_context.speckle_client.branch.create(
                stream_id=project_id, name=RESULT_BRANCH, description=""
            )
        else:
            br_id = existing_branch.id
        # commitObj.elements.append(base)

        print(f"Branch_id={br_id}")
        # print(f"CommitObj={commitObj}")

        automate_context.create_new_version_in_project(
            commitObj, br_id, "Context from Automate"
        )
        print(
            f"Created id={automate_context._automation_result.result_versions[len(automate_context._automation_result.result_versions)-1]}"
        )
        # automate_context.compose_result_view()
        automate_context._automation_result.result_view = f"{automate_context.automation_run_data.speckle_server_url}/projects/{automate_context.automation_run_data.project_id}/models/{automate_context.automation_run_data.model_id},{br_id}"
        # https://latest.speckle.systems/

        automate_context.mark_run_success("Created 3D context")
    except Exception as ex:
        automate_context.mark_run_failed(f"Failed to create 3d context cause: {ex}")


# make sure to call the function with the executor
if __name__ == "__main__":
    # NOTE: always pass in the automate function by its reference, do not invoke it!

    # pass in the function reference with the inputs schema to the executor
    execute_automate_function(automate_function, FunctionInputs)

    # if the function has no arguments, the executor can handle it like so
    # execute_automate_function(automate_function_without_inputs)
