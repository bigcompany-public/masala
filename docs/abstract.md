# Abstract

Before diving in, let's explain the framework proposed by Masala.

## The problem Masala tries to solve

The lifespan of an asset typically looks like that:

- 3D Modeler creates an asset without materials.
- A file is exported, and serves as a base for the surfacing artist.
- rince and repeat for all the following departments.

This asset pipeline has multiple flaws: 

1. Departments are dependant on each others. When the asset's mesh is ready, a lot of departments *should* be able to work right away (surfacing, grooming, rigging, cfx...) but aren't able to do so because they are waiting another deparment to finish their job.
2. Some changes may occur in the wrong department: textures may change because of the grooming artist, or adjustments to the mesh may be done to accomodate rigging, causing the pipeline to go all the way back, or involve cross-departments shenanigans.
3. All across the lifespan of the asset, a lot of "derived" representations of the asset can be generated, for purposes like client validation, variations, level of detail, quality checks, tests... which can require to bend the assets in all sorts of ways.
4. Each department carries the mess of previous departments, leading into all sorts of bugs and files that end up way heavier than they should.

## How Masala addresses it

Masala is build around the concept of `AssetBlocks`, which are small units of the asset that are versioned and stored in an `AssetBlockLibrary`. 

To generate these `AssetBlocks`, the user will use `Exporters` designed to export only the relevant data (for instance, the mesh stripped from its materials and constraints), and possibly metadatas to add extra details along the exported `AssetBlock`

!!! note
    An `AssetBlock` can have multiple `Exporters`. For instance, and `Exporter` for Blender, and one for Maya.

Now, the goal is to combine the latest version of each of these parts: this is where the `Assembler` comes into play.

The `Assembler` uses `Operators` that indicate how `AssetBlocks` should be imported, combined, and tweaked to end up with the desired result.

!!! success
    With this framework the entire team contributes to an asset, independently of the department they are working in.
    At any point during the fabrication of an asset, any representation of the asset (finalized asset, proxy, variation...) can be rebuilt from scratch in a matter of seconds.

## Caveats

Masala is centered around the idea of granularity, where each `AssetBlock` acts as a lean single-purpose component... But assets can be complex and intertwined, especially when one wants to get the most of a DCC's features. As a result, it is often wise to know where Masala's modular design should stop, and where a careful hand-crafted assembly should start.