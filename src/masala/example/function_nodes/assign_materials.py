from masala.api import FunctionNodeDescription, Input


def callback(materials: list, geometries: list, assignment_metadata: dict):
    print(f"assigning materials to {geometries}")
    return


assign_materials = FunctionNodeDescription(
    name="AssignMaterials",
    label="Assign Materials",
    callback=callback,
    inputs=[
        Input(kwarg="geometries", label="Geometries", typ="list", mandatory=True),
        Input(kwarg="materials", label="Materials", typ="list", mandatory=True),
        Input(kwarg="assignment_metadata", label="Metadata", typ="dict", mandatory=True),
    ],
)
