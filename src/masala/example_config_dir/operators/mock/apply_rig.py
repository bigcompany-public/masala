from masala import Input, Operator


def callback(controllers: list, geometries: list, assignment_metadata: dict):
    print(f"assigning rig to {geometries}")
    return


apply_rig = Operator(
    name="ApplyRig",
    label="Apply Rig",
    callback=callback,
    inputs=[
        Input(kwarg="geometries", label="Geometries", typ=list, mandatory=True),
        Input(kwarg="controllers", label="Controllers", typ=list, mandatory=True),
        Input(kwarg="assignment_metadata", label="Metadata", typ=dict, mandatory=True),
    ],
)
