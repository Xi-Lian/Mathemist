import os


def _patch_langgraph_node_alias():
    """
    Local runtime compatibility patch:
    if a node name conflicts with a state key, auto-create an alias and remap edges.
    This avoids changing existing backend business files.
    """
    from langgraph.graph.state import StateGraph

    if getattr(StateGraph, "_mathemist_local_alias_patch", False):
        return

    original_add_node = StateGraph.add_node
    original_add_edge = StateGraph.add_edge
    original_add_conditional_edges = StateGraph.add_conditional_edges

    def get_aliases(graph_obj):
        aliases = getattr(graph_obj, "_mathemist_node_aliases", None)
        if aliases is None:
            aliases = {}
            setattr(graph_obj, "_mathemist_node_aliases", aliases)
        return aliases

    def remap_name(graph_obj, name):
        if name is None:
            return None
        aliases = get_aliases(graph_obj)
        return aliases.get(name, name)

    def add_node_with_alias(self, node, action=None, *, metadata=None, input=None, retry=None):
        try:
            return original_add_node(
                self,
                node,
                action,
                metadata=metadata,
                input=input,
                retry=retry,
            )
        except ValueError as exc:
            message = str(exc)
            if "already being used as a state key" not in message or not isinstance(node, str):
                raise

            aliases = get_aliases(self)
            if node in aliases:
                alias = aliases[node]
            else:
                alias = f"{node}__node"
                counter = 2
                while alias in aliases.values():
                    alias = f"{node}__node_{counter}"
                    counter += 1
                aliases[node] = alias

            return original_add_node(
                self,
                alias,
                action,
                metadata=metadata,
                input=input,
                retry=retry,
            )

    def add_edge_with_alias(self, start_key, end_key):
        if isinstance(start_key, list):
            mapped_start = [remap_name(self, key) for key in start_key]
        else:
            mapped_start = remap_name(self, start_key)
        mapped_end = remap_name(self, end_key)
        return original_add_edge(self, mapped_start, mapped_end)

    def add_conditional_edges_with_alias(self, source, path, path_map=None):
        mapped_source = remap_name(self, source)

        mapped_path_map = path_map
        if isinstance(path_map, dict):
            mapped_path_map = {key: remap_name(self, value) for key, value in path_map.items()}
        elif isinstance(path_map, list):
            mapped_path_map = [remap_name(self, value) for value in path_map]

        return original_add_conditional_edges(
            self,
            mapped_source,
            path,
            mapped_path_map,
        )

    StateGraph.add_node = add_node_with_alias
    StateGraph.add_edge = add_edge_with_alias
    StateGraph.add_conditional_edges = add_conditional_edges_with_alias
    StateGraph._mathemist_local_alias_patch = True


def main():
    _patch_langgraph_node_alias()

    os.environ.setdefault("PORT", "8000")
    os.environ.setdefault("HOST", "0.0.0.0")

    from main import app
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    print(f"🚀 启动后端服务器: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
