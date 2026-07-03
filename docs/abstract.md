# Abstract

Before diving in, let us introduce the framework proposed by Masala.

## The problem Masala aims to solve

The lifecycle of an asset typically looks like this:

- A 3D modeler creates an asset without materials.
- The file is exported as a starting point for the surfacing artist.
- The process repeats across the following departments.

This pipeline has several shortcomings:

1. Departments depend on one another. When the asset mesh is ready, many departments (such as surfacing, grooming, rigging, and cfx) **should** be able to begin work immediately, but they often cannot because they are waiting for another department to finish its part.
2. Changes may be introduced in the wrong department. For example, textures may be adjusted by the grooming artist, or the mesh may be modified to accommodate rigging, forcing the pipeline to move backward or requiring cross-department coordination.
3. Throughout the asset lifecycle, many derived representations are generated for purposes such as client review, variations, level of detail, quality checks, and testing. These often require reshaping the asset in different ways.
4. Each department inherits the complexity introduced by previous ones, which can lead to bugs and files that become unnecessarily heavy.
5. The person or department that ends up at the end of the assembly line often becomes responsible for exporting the final asset. This can turn them into a bottleneck, as they are then accountable for a wide range of issues and decisions.

## How Masala addresses it

Masala is built around the concept of `AssetBlocks`, which are small, versioned units of an asset stored in an `AssetBlockLibrary`.

To create these `AssetBlocks`, users employ `Exporters` designed to export only the relevant data (for example, a mesh stripped of its materials and constraints) along with optional metadata that adds context to the exported `AssetBlock`.

!!! note
    An `AssetBlock` can have multiple `Exporters`. For instance, one `Exporter` for Blender and another for Maya.

The goal is now to combine the latest version of each part. This is where the `Assembler` comes into play.

The `Assembler` uses `Operators` to define how `AssetBlocks` should be imported, combined, and adjusted to produce the desired result.

!!! success
    With this framework, the entire team can contribute to an asset independently of the department they work in.
    At any point in the asset creation process, any representation of the asset (such as a final asset, proxy, or variation) can be rebuilt from scratch in a matter of seconds.

## Caveats

Masala is centered on the idea of granularity, where each `AssetBlock` acts as a lean, single-purpose component. However, assets can be complex and deeply interconnected, especially when one wants to take full advantage of a DCC's features. As a result, it is often important to know where Masala's modular design should stop and where a more carefully handcrafted assembly should begin.