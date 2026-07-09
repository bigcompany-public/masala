from pynput.keyboard import Controller, Key
from qtpy import QtCore
from qtpy.QtWidgets import QFileDialog

from masala.nodegraph import AssemblerGraph


def zoom_in(graph: AssemblerGraph):
    """
    Set the node graph to zoom in by 0.1
    """
    zoom = graph.get_zoom() + 0.1
    graph.set_zoom(zoom)


def zoom_out(graph: AssemblerGraph):
    """
    Set the node graph to zoom in by 0.1
    """
    zoom = graph.get_zoom() - 0.2
    graph.set_zoom(zoom)


def reset_zoom(graph: AssemblerGraph):
    """
    Reset zoom level.
    """
    graph.reset_zoom()


def layout_h_mode(graph: AssemblerGraph):
    """
    Set node graph layout direction to horizontal.
    """
    graph.set_layout_direction(0)


def layout_v_mode(graph: AssemblerGraph):
    """
    Set node graph layout direction to vertical.
    """
    graph.set_layout_direction(1)


def open_session(graph: AssemblerGraph):
    """
    Prompts a file open dialog to load a session.
    """
    current = graph.current_session()
    graph.recipes_dir.mkdir(exist_ok=True, parents=True)
    file_path = QFileDialog.getOpenFileName(
        graph._viewer,
        caption="Open Graph",
        dir=current or graph.recipes_dir.as_posix(),
        filter="*.json",
    )[0]

    # Fix NodeGraphQt bug, that believes the Ctrl Button is pressed forever
    keyboard = Controller()
    keyboard.press(Key.ctrl_l)
    keyboard.release(Key.ctrl_l)

    if not file_path:
        return

    graph.load_session(file_path)


def import_session(graph: AssemblerGraph):
    """
    Prompts a file open dialog to load a session.
    """
    current = graph.current_session()
    graph.recipes_dir.mkdir(exist_ok=True, parents=True)
    file_path = QFileDialog.getOpenFileName(
        graph._viewer,
        caption="Open Graph",
        dir=current or graph.recipes_dir.as_posix(),
        filter="*.json",
    )[0]

    # Fix NodeGraphQt bug, that believes the Ctrl Button is pressed forever
    keyboard = Controller()
    keyboard.press(Key.ctrl_l)
    keyboard.release(Key.ctrl_l)

    if not file_path:
        return

    graph.import_session(file_path)


def save_session(graph: AssemblerGraph):
    """
    Prompts a file save dialog to serialize a session if required.
    """
    current = graph.current_session()
    if current:
        graph.save_session(current)
        msg = "Session layout saved:\n{}".format(current)
        viewer = graph.viewer()
        viewer.message_dialog(msg, title="Session Saved")
    else:
        save_session_as(graph)


def save_session_as(graph: AssemblerGraph):
    """
    Prompts a file save dialog to serialize a session.
    """
    graph.recipes_dir.mkdir(exist_ok=True, parents=True)
    file_path = QFileDialog.getSaveFileName(
        parent=graph._viewer,
        caption="Save Graph As",
        dir=graph.recipes_dir.as_posix(),
        filter="*.json",
    )[0]

    # Fix NodeGraphQt bug, that believes the Ctrl Button is pressed forever
    keyboard = Controller()
    keyboard.press(Key.ctrl_l)
    keyboard.release(Key.ctrl_l)

    if not file_path:
        return

    graph.save_session(file_path)


def clear_session(graph: AssemblerGraph):
    """
    Prompts a warning dialog to new a node graph session.
    """
    if graph.question_dialog("Clear Current Session?", "Clear Session"):
        graph.clear_session()


def quit_qt(graph: AssemblerGraph):
    """
    Quit the Qt application.
    """
    QtCore.QCoreApplication.quit()


def clear_undo(graph: AssemblerGraph):
    """
    Prompts a warning dialog to clear undo.
    """
    viewer = graph.viewer()
    msg = "Clear all undo history, Are you sure?"
    if viewer.question_dialog("Clear Undo History", msg):
        graph.clear_undo_stack()


def copy_nodes(graph: AssemblerGraph):
    """
    Copy nodes to the clipboard.
    """
    graph.copy_nodes()


def cut_nodes(graph: AssemblerGraph):
    """
    Cut nodes to the clip board.
    """
    graph.cut_nodes()


def paste_nodes(graph: AssemblerGraph):
    """
    Pastes nodes copied from the clipboard.
    """
    # by default the graph will inherite the global style
    # from the graph when pasting nodes.
    # to disable this behaviour set `adjust_graph_style` to False.
    graph.paste_nodes(adjust_graph_style=False)


def delete_nodes_and_pipes(graph: AssemblerGraph):
    """
    Delete selected nodes and connections.
    """
    graph.delete_nodes(graph.selected_nodes())
    for pipe in graph.selected_pipes():
        pipe[0].disconnect_from(pipe[1])


def extract_nodes(graph: AssemblerGraph):
    """
    Extract selected nodes.
    """
    graph.extract_nodes(graph.selected_nodes())


def clear_node_connections(graph: AssemblerGraph):
    """
    Clear port connection on selected nodes.
    """
    graph.undo_stack().beginMacro("clear selected node connections")
    for node in graph.selected_nodes():
        for port in node.input_ports() + node.output_ports():
            port.clear_connections()
    graph.undo_stack().endMacro()


def select_all_nodes(graph: AssemblerGraph):
    """
    Select all nodes.
    """
    graph.select_all()


def clear_node_selection(graph: AssemblerGraph):
    """
    Clear node selection.
    """
    graph.clear_selection()


def invert_node_selection(graph: AssemblerGraph):
    """
    Invert node selection.
    """
    graph.invert_selection()


def disable_nodes(graph: AssemblerGraph):
    """
    Toggle disable on selected nodes.
    """
    graph.disable_nodes(graph.selected_nodes())


def duplicate_nodes(graph: AssemblerGraph):
    """
    Duplicated selected nodes.
    """
    graph.duplicate_nodes(graph.selected_nodes())


def expand_group_node(graph: AssemblerGraph):
    """
    Expand selected group node.
    """
    selected_nodes = graph.selected_nodes()
    if not selected_nodes:
        graph.message_dialog('Please select a "GroupNode" to expand.')
        return
    graph.expand_group_node(selected_nodes[0])


def fit_to_selection(graph: AssemblerGraph):
    """
    Sets the zoom level to fit selected nodes.
    """
    graph.fit_to_selection()


def show_undo_view(graph: AssemblerGraph):
    """
    Show the undo list widget.
    """
    graph.undo_view.show()


def curved_pipe(graph: AssemblerGraph):
    """
    Set node graph pipes layout as curved.
    """
    from NodeGraphQt.constants import PipeLayoutEnum

    graph.set_pipe_style(PipeLayoutEnum.CURVED.value)


def straight_pipe(graph: AssemblerGraph):
    """
    Set node graph pipes layout as straight.
    """
    from NodeGraphQt.constants import PipeLayoutEnum

    graph.set_pipe_style(PipeLayoutEnum.STRAIGHT.value)


def angle_pipe(graph: AssemblerGraph):
    """
    Set node graph pipes layout as angled.
    """
    from NodeGraphQt.constants import PipeLayoutEnum

    graph.set_pipe_style(PipeLayoutEnum.ANGLE.value)


def bg_grid_none(graph: AssemblerGraph):
    """
    Turn off the background patterns.
    """
    from NodeGraphQt.constants import ViewerEnum

    graph.set_grid_mode(ViewerEnum.GRID_DISPLAY_NONE.value)


def bg_grid_dots(graph: AssemblerGraph):
    """
    Set background node graph background with grid dots.
    """
    from NodeGraphQt.constants import ViewerEnum

    graph.set_grid_mode(ViewerEnum.GRID_DISPLAY_DOTS.value)


def bg_grid_lines(graph: AssemblerGraph):
    """
    Set background node graph background with grid lines.
    """
    from NodeGraphQt.constants import ViewerEnum

    graph.set_grid_mode(ViewerEnum.GRID_DISPLAY_LINES.value)


def layout_graph_down(graph: AssemblerGraph):
    """
    Auto layout the nodes down stream.
    """
    nodes = graph.selected_nodes() or graph.all_nodes()
    graph.auto_layout_nodes(nodes=nodes, down_stream=True)


def layout_graph_up(graph: AssemblerGraph):
    """
    Auto layout the nodes up stream.
    """
    nodes = graph.selected_nodes() or graph.all_nodes()
    graph.auto_layout_nodes(nodes=nodes, down_stream=False)


def toggle_node_search(graph: AssemblerGraph):
    """
    show/hide the node search widget.
    """
    graph.toggle_node_search()


def run_selected_nodes(graph: AssemblerGraph):
    graph.execute_nodes(graph.selected_nodes())


def evaluate_selected_nodes(graph: AssemblerGraph):
    graph.evaluate_nodes(graph.selected_nodes())


def evaluate_graph(graph: AssemblerGraph):
    graph.evaluate()


def show_logs(graph: AssemblerGraph):
    for node in graph.selected_nodes():
        node.show_logs()

    # Fix NodeGraphQt bug, that believes the Ctrl Button is pressed forever
    keyboard = Controller()
    keyboard.press(Key.ctrl_l)
    keyboard.release(Key.ctrl_l)
