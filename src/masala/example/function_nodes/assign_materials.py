from masala.api import Input, Operator


def callback(materials: list, geometries: list, assignment_metadata: dict):
    print(f"assigning materials to {geometries}")
    return


assign_materials = Operator(
    name="AssignMaterials",
    label="Assign Materials",
    callback=callback,
    inputs=[
        Input(kwarg="geometries", label="Geometries", typ=list, mandatory=True),
        Input(kwarg="materials", label="Materials", typ=list, mandatory=True),
        Input(kwarg="assignment_metadata", label="Metadata", typ=dict, mandatory=True),
    ],
)
