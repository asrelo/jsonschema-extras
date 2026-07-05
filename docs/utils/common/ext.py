from docutils import nodes


def get_current_heading_level(node: nodes.Node | None) -> int:
    level = 0
    while node is not None:
        if isinstance(node, nodes.section):
            level += 1
        node = node.parent
    return level
