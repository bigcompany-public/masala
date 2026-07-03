# Masala Documentation

## What is Masala?

A system for creating assets from modular building blocks (`AssetBlocks`) that are exported independently and recombined at will. This approach improves task parallelization and streamlines the creation of multiple variations of the same asset.

![masala_exporter](img/masala_exporter.png)

![masala_assembler](img/masala_assembler.png)

## What Makes Masala So Spicy?

Masala is designed to solve issues of waterfall asset creation, where the dependency between departments (modeling, surfacing, rigging...) creates friction:

- :clock10: artists waiting for another department to publish a file.
- :arrows_counterclockwise: circular dependency between departments
- :lock: coupling and heavy files due to asset variations and levels of detail
- :gear: steps not being done in the same DCC

Masala solves these issues by relying on `AssetBlocks` (mesh, materials, rig constraints...) that are **not** linked to a particular department. For instance, a grooming artist can adjust a texture, and a rigging artist may add a few edges, and changes will be propagated to other departments.

AssetBlocks also allow to quickly create various representations of an asset (model without textures, lods...) on the fly, and to create variations of assets without the burden of dependency.

## What Masala Is Not?

Masala is only a framework, and does not provide a turnkey solution for engineering an asset: the DCCs, export formats, and assembly logic are entirely up to you.

---

!!! info ""
    <a href="Next Section"> <div style="text-align: right; font-weight: bold"> [Next Section : Abstract](./abstract.md) </div>
