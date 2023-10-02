"""This module contains the business logic of the function.

use the automation_context module to wrap your function in an Autamate context helper
"""

from pydantic import Field
from speckle_automate import (
    AutomateBase,
    AutomationContext,
    execute_automate_function,
)

from specklepy.transports.server import ServerTransport
from specklepy.api.operations import receive
from specklepy.api.client import SpeckleClient
from specklepy.api.models import Branch
#from flatten import flatten_base
from run_context import run as run_context

class FunctionInputs(AutomateBase):
    """These are function author defined values.

    Automate will make sure to supply them matching the types specified here.
    Please use the pydantic model schema to define your inputs:
    https://docs.pydantic.dev/latest/usage/models/
    """

    radius_in_meters: str = Field(
        title="Radius in meters",
        description=(
            "Radius from the Model location,"
            " derived from Revit model lat, lon."
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
    # the context provides a conveniet way, to receive the triggering version
    r'''
    version_root_object = automate_context.receive_version()
    count = 0
    for b in flatten_base(version_root_object):
        if b.speckle_type == function_inputs.forbidden_speckle_type:
            if not b.id:
                raise ValueError("Cannot operate on objects without their id's.")
            automate_context.add_object_error(
                b.id,
                "This project should not contain the type: " f"{b.speckle_type}",
            )
            count += 1

    if count > 0:
        # this is how a run is marked with a failure cause
        automate_context.mark_run_failed(
            "Automation failed: "
            f"Found {count} object that have one of the forbidden speckle types: "
            f"{function_inputs.forbidden_speckle_type}"
        )

    else:
        automate_context.mark_run_success("No forbidden types found.")
    ''' 
    # schema comes from automate 
    project_data = automate_context.automation_run_data #SpeckleProjectData.model_validate_json(speckle_project_data)
    # defined by function author (above). Optional 
    #inputs = FunctionInputs.model_validate_json(function_inputs)

    base = automate_context.receive_version()

    # client = SpeckleClient(project_data.speckle_server_url, use_ssl=False)
    #client.authenticate_with_token(automate_context._speckle_token)
    #client = automate_context.speckle_client
    # branch: Branch = client.branch.get(project_data.project_id, project_data.model_id, 1)

    #server_transport = ServerTransport(project_data.project_id, client)
    #base = receive(branch.commits.items[0].referencedObject, server_transport)
    
    #base = automate_context.receive_version()
    run_context(automate_context.speckle_client, server_transport, base, float(function_inputs.radius_in_meters))
    automate_context.mark_run_success("Hopefully there were no errors.")

    # if the function generates file results, this is how it can be
    # attached to the Speckle project / model
    # automate_context.store_file_result("./report.pdf")


def automate_function_without_inputs(automate_context: AutomationContext) -> None:
    """A function example without inputs.

    If your function does not need any input variables,
     besides what the automation context provides,
     the inputs argument can be omitted.
    """
    pass


# make sure to call the function with the executor
if __name__ == "__main__":
    # NOTE: always pass in the automate function by its reference, do not invoke it!

    # pass in the function reference with the inputs schema to the executor
    execute_automate_function(automate_function, FunctionInputs)

    # if the function has no arguments, the executor can handle it like so
    # execute_automate_function(automate_function_without_inputs)
