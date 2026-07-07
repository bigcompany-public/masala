# Tools

## Masala Exporter

![masala_exporter](img/masala_exporter.png)

Masala Exporter is really straightforward: select the Exporters you want to execute and click `Export`.

!!! tip
    The Exporter Area has an expanded selection mode, so the following shortcuts are available.

    - `Ctrl` + `click` -> additive selection
    - `Shift` + `click` -> contiguous selection
    - `Ctrl` + `A` -> select all
    - `Shift` + `up/down arrow` -> extend selection up/down
    - `Ctrl` + `Space` -> unselect last selected item

### Logs

You can inspect the logs of each Exporter individually by clicking on the `Show Logs` button.

![exporter_logs](img/exporter_logs.png)

### Additional Options

A few additional options can be accessed by right-clicking the Exporters Area.

![exporter_menu](img/exporter_menu.png)

## Masala Assembler

Masala Assembler is a node graph that describes the steps that must be taken to obtain the desired result.

Keep in mind that the end result may not always be a finalized asset, as you can also write Recipes to create:

- asset variations
- levels of detail
- representations for validation
- asset debugging workflows
- the list goes on...

![masala_assembler](img/masala_assembler.png)

### Navigation

- `Middle Click` -> `Move`
- `Mouse Wheel` -> `Zoom In / Zoom Out`
- `Click` -> `Select Node`
- `Shift + Click` -> `Add Node To Selection`

### Actions

You can access all available actions (and see their shortcuts) by right-clicking the node graph area.

![assembler_menu](img/assembler_menu.png)

### AssetBlock Nodes

Pressing `Tab` shows the Node Search. From there, you can access all AssetBlocks under the `AssetBlocks` submenu, or search them by name.

![masala_mesh_assembler](img/masala_mesh_assembler.png)

There are two ways of getting your AssetBlock file:

- By manually picking the desired file using the `Browse` button
    ![assembler_browse](img/assembler_browse.png)
- By providing fields that allow Lucent to automatically find files matching the AssetBlock's naming convention
    ![assembler_fields](img/assembler_fields.png)

### Operators

Similar to AssetBlocks, press `Tab` to show the Node Search. From there, you can access all Operators under the `Operators` submenu, or search them by name.

![assembler_operators](img/assembler_operators.png)

### Executing Nodes

To execute the entire graph, you can press the `Execute Graph` button or press `Ctrl + Shift + E`.

If you need more fine-tuned control over what is executed, you can:

- Evaluate Selected Nodes (meaning "execute selected nodes and their parents") by pressing `Ctrl + E`
- Run Single Nodes by clicking on the `Run Button` or by pressing `Ctrl + R`

#### About Node Graph Evaluation Order

The order in which Operators are executed depends on their connections: if any of `Operator1`'s output plugs is connected to any of `Operator2`'s input plugs, then `Operator2` cannot run until `Operator1` has been executed.

Evaluating the entire graph or a node selection automatically computes the order in which Operators should run.

You can enforce evaluation order by using the `Dependencies` input plug of Operator nodes.

!!! tip "In this example, Operator :three: needs both Operators :one: and :two: before it can be executed"
    ![evaluation_order](img/evaluation_order.png)

---

!!! info ""
    <a href="Next Section"> <div style="text-align: right; font-weight: bold"> [Next Section : DCC Implementations](./dccs.md) </div>