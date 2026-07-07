from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

import bpy
from bpy.types import Collection, Material, Mesh, Object

from masala.api import Exporter
from masala.example.assetblocks_dir.staticmesh import static_mesh

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")


@dataclass
class MaterialSlotInfo:
    """Describes one material slot on a mesh object."""

    slot_index: int
    material_name: Optional[str]
    # Face indices that use this slot (empty = slot applies to whole mesh)
    face_indices: list[int] = field(default_factory=list)


@dataclass
class MeshMaterialMapping:
    """Full mapping for a single mesh object."""

    object_name: str
    mesh_data_name: str
    collection_path: str
    material_slots: list[MaterialSlotInfo] = field(default_factory=list)


class MaterialExporter:
    """
    Orchestrates material discovery, export, and manifest generation for
    all mesh objects found under the  myAsset/staticMesh  collection hierarchy.
    """

    def __init__(
        self,
        output_path: str | Path,
    ) -> None:
        self.current_path = get_path()
        self.temp_dir = self.current_path.parent / "temp"
        self.temp_blend_path = self.temp_dir / self.current_path.name
        self.material_blend_path = Path(output_path)

        self._mesh_objects: list[Object] = []
        self._materials: list[Material] = []
        self._mappings: list[MeshMaterialMapping] = []

    def run(self) -> None:
        """Execute the full export pipeline."""
        log.info("Saving temporary scene")
        self.save_temp_scene()

        log.info("Packing external resources")
        self.pack_resources()

        log.info("Collecting mesh objects")
        self._mesh_objects = self.collect_mesh_objects()
        log.info("  Found %d mesh object(s).", len(self._mesh_objects))

        log.info("Listing materials")
        self._materials = self.list_materials(self._mesh_objects)
        log.info("  Found %d unique material(s).", len(self._materials))

        log.info("Exporting materials")
        self.export_materials(self._materials)

        log.info("Building mesh↔material manifest")
        self._mappings = self.build_mappings(self._mesh_objects)
        self.write_manifest(self._mappings)

        log.info("Done.  Outputs written to: %s", self.output_dir)

    def save_temp_scene(self) -> None:
        """
        Save the current .blend file to a temporary path so the original is
        never overwritten and subsequent operations work on a known-good copy.
        """
        bpy.ops.wm.save_as_mainfile(filepath=str(self.temp_blend_path), copy=True)
        log.info("  Temporary scene saved → %s", self.temp_blend_path)

    def pack_resources(self) -> None:
        """
        Pack all external resources (textures, fonts, sounds, volumes) into
        the .blend data-block so the file is self-contained.
        """
        bpy.ops.file.pack_all()
        log.info("  All external resources packed.")

    def collect_mesh_objects(self) -> list[Object]:
        """
        Return every MESH object that lives inside
        ``myAsset/staticMesh`` (or any of its sub-collections).

        The search is name-based: first locate the top-level collection whose
        name starts with ``ROOT_COLLECTION``, then find the child collection
        whose name starts with ``STATIC_MESH_COLLECTION``.
        """
        root = self._find_collection(bpy.context.scene.collection, self.ROOT_COLLECTION)
        if root is None:
            raise ValueError(f"Collection '{self.ROOT_COLLECTION}' not found in the scene.")

        static_mesh_col = self._find_collection(root, self.STATIC_MESH_COLLECTION)
        if static_mesh_col is None:
            raise ValueError(
                f"Sub-collection '{self.STATIC_MESH_COLLECTION}' not found under '{self.ROOT_COLLECTION}'."
            )

        mesh_objects: list[Object] = []
        self._collect_meshes_recursive(static_mesh_col, mesh_objects)
        return mesh_objects

    def list_materials(self, mesh_objects: list[Object]) -> list[Material]:
        """
        Return the deduplicated, name-sorted list of all materials that are
        referenced by at least one material slot across the given mesh objects.
        """
        seen: set[str] = set()
        materials: list[Material] = []

        for obj in mesh_objects:
            for slot in obj.material_slots:
                mat = slot.material
                if mat is not None and mat.name not in seen:
                    seen.add(mat.name)
                    materials.append(mat)

        materials.sort(key=lambda m: m.name)
        for mat in materials:
            log.info("  Material: %s", mat.name)
        return materials

    def export_materials(self, materials: list[Material]) -> None:
        """
        Write a .blend library file that contains ONLY the given materials
        (no meshes, objects, scenes, cameras, lights).

        The file can later be appended/linked into other projects via
        File → Append → <exported_materials.blend> → Material → <name>.
        """
        if not materials:
            log.warning("  No materials to export – skipping.")
            return

        mat_names = {m.name for m in materials}

        # bpy.data.libraries.write expects a set of data-block references.
        data_blocks: set[Material] = {m for m in bpy.data.materials if m.name in mat_names}

        bpy.data.libraries.write(
            str(self.material_blend_path),
            data_blocks,
            path_remap="RELATIVE",
            fake_user=True,
        )
        log.info(
            "  %d material(s) exported → %s",
            len(data_blocks),
            self.material_blend_path,
        )

    def build_mappings(self, mesh_objects: list[Object]) -> list[MeshMaterialMapping]:
        """
        For each mesh object, build a :class:`MeshMaterialMapping` that records:

        * which material occupies each slot
        * which polygon (face) indices are assigned to each slot

        If the mesh uses the same material for every face (no per-face
        assignment) the ``face_indices`` list is left empty.
        """
        mappings: list[MeshMaterialMapping] = []

        for obj in mesh_objects:
            mesh: Mesh = obj.data  # type: ignore[assignment]
            collection_path = self._get_collection_path(obj)

            # Build per-slot face-index lists
            slot_faces: dict[int, list[int]] = {i: [] for i in range(len(obj.material_slots))}
            for poly_index, poly in enumerate(mesh.polygons):
                slot_faces[poly.material_index].append(poly_index)

            # Determine whether all faces share the same slot (no real selection)
            all_same = len(slot_faces) <= 1

            slots: list[MaterialSlotInfo] = []
            for slot_index, slot in enumerate(obj.material_slots):
                face_list = [] if all_same else slot_faces.get(slot_index, [])
                slots.append(
                    MaterialSlotInfo(
                        slot_index=slot_index,
                        material_name=slot.material.name if slot.material else None,
                        face_indices=face_list,
                    )
                )

            mappings.append(
                MeshMaterialMapping(
                    object_name=obj.name,
                    mesh_data_name=mesh.name,
                    collection_path=collection_path,
                    material_slots=slots,
                )
            )

        return mappings

    def write_manifest(self, mappings: list[MeshMaterialMapping]) -> None:
        """
        Serialise the mesh↔material mappings to a pretty-printed JSON file.

        Schema (per mesh entry):
        ::

            {
              "object_name": "Cube.001",
              "mesh_data_name": "Cube",
              "collection_path": "myAsset/staticMesh",
              "material_slots": [
                {
                  "slot_index": 0,
                  "material_name": "M_Wood",
                  "face_indices": [0, 1, 4, 5]   // empty = whole mesh
                },
                ...
              ]
            }
        """
        payload = [asdict(m) for m in mappings]
        with self.manifest_path.open("w", encoding="utf-8") as fp:
            json.dump(payload, fp, indent=2, ensure_ascii=False)
        log.info("  Manifest written → %s", self.manifest_path)

    @staticmethod
    def _find_collection(
        parent: Collection,
        name_prefix: str,
    ) -> Optional[Collection]:
        """
        Breadth-first search for the first collection whose name matches
        *name_prefix* exactly or starts with it (case-sensitive).
        Returns ``None`` if nothing is found.
        """
        queue: list[Collection] = list(parent.children)
        while queue:
            col = queue.pop(0)
            if col.name == name_prefix or col.name.startswith(name_prefix):
                return col
            queue.extend(col.children)
        return None

    @staticmethod
    def _collect_meshes_recursive(
        collection: Collection,
        result: list[Object],
    ) -> None:
        """Append all MESH objects from *collection* and its descendants."""
        for obj in collection.objects:
            if obj.type == "MESH":
                result.append(obj)
        for child in collection.children:
            MaterialExporter._collect_meshes_recursive(child, result)

    @staticmethod
    def _get_collection_path(obj: Object) -> str:
        """
        Return a slash-separated path of the collection hierarchy that
        directly contains *obj*, e.g. ``"myAsset/staticMesh/props"``.
        Falls back to the object name if no collection is found.
        """
        for col in bpy.data.collections:
            if obj.name in col.objects:
                # Attempt to build the ancestry path
                ancestors: list[str] = [col.name]
                parent_col = MaterialExporter._find_parent_collection(col)
                while parent_col is not None:
                    ancestors.insert(0, parent_col.name)
                    parent_col = MaterialExporter._find_parent_collection(parent_col)
                return "/".join(ancestors)
        return obj.name  # fallback

    @staticmethod
    def _find_parent_collection(
        target: Collection,
    ) -> Optional[Collection]:
        """Return the immediate parent collection of *target*, or ``None``."""
        for col in bpy.data.collections:
            if target.name in [c.name for c in col.children]:
                return col
        # Also check the scene master collection
        if target.name in [c.name for c in bpy.context.scene.collection.children]:
            return None  # scene root has no collection parent
        return None


def get_path() -> Path:
    path = bpy.data.filepath
    if not path:
        raise RuntimeError("Cannot extract current path. Please save your scene first")
    return Path(path)


def export(path: Path):
    exporter = MaterialExporter()
    exporter.run()


def meta() -> dict:
    return {"hello": "world"}


static_mesh_exporter = Exporter(
    static_mesh, current_path_callback=get_path, export_callback=export, metadata_callback=meta
)
