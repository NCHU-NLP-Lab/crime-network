import multiprocessing as mp
import os

from pymongo import MongoClient

MONGO_CONNECTION_CONFIG = {
    "host": os.environ.get("MONGO_HOST"),
    "port": int(os.environ.get("MONGO_PORT")),
    "username": os.environ.get("MONGO_USERNAME"),
    "password": os.environ.get("MONGO_PASSWORD"),
}

MONGO_DB_NAMES = {
    "database": os.environ.get("MONGO_DB"),
    "node": os.environ.get("MONGO_NODE"),
    "edge": os.environ.get("MONGO_EDGE"),
    "verdict": os.environ.get("MONGO_VERDICT"),
}


def filter_sys(edges, sys):
    """
    Filter edges with only the specified sys (民事 or 刑事)

    sys: Verdict with sys to keep

    return None, modify edges
    """
    if sys not in ["民事", "刑事"]:
        raise ValueError(f"Invalid sys: {sys}")
    broken_edges = []
    for edge_index, edge in enumerate(edges):
        filter_indexes = []
        for verdict_index in range(len(edge["sys"])):
            if edge["sys"][verdict_index] != sys:
                filter_indexes.append(verdict_index)
        filter_indexes.reverse()  # 從大的index pop到小的，不然index會位移
        for field in ["reason", "date", "court", "no", "sys", "type", "v_id"]:
            for verdict_index in filter_indexes:
                edge[field].pop(verdict_index)
        edge["weight"] -= len(filter_indexes)
        if edge["weight"] == 0:
            broken_edges.append(edge_index)
    broken_edges.reverse()
    for broken_index in broken_edges:
        edges.pop(broken_index)


def node_process(name):
    client = MongoClient(**MONGO_CONNECTION_CONFIG)
    this_Node = client[MONGO_DB_NAMES["database"]][MONGO_DB_NAMES["node"]].find(
        {"name": name}
    )[0]
    this_Node = {
        "name": name,
        "v_id": this_Node["v_id"],
        "reason": this_Node["reason"],
        "sys": this_Node["sys"],
        "court": this_Node["court"],
        "type": this_Node["type"],
        "no": this_Node["no"],
        "date": this_Node["date"],
    }
    return this_Node


def get_node(prisoner, Node, Edge, sys):
    """
    Query all edges connect from `prisoner`, and store to `Edge`.
    If `to_Name` of the edges is not already in `Node`,
    append it for next level iteration.

    return None, modify `Node` and `Edge`
    """
    client = MongoClient(**MONGO_CONNECTION_CONFIG)
    if prisoner not in Node:
        Node.append(prisoner)
    if prisoner not in Edge:
        prisoner_edges = list(
            client[MONGO_DB_NAMES["database"]][MONGO_DB_NAMES["edge"]].find(
                {"from_Name": prisoner}
            )
        )
        if sys:
            filter_sys(prisoner_edges, sys)
        Edge[prisoner] = prisoner_edges
    else:
        prisoner_edges = Edge[prisoner]

    for e in prisoner_edges:
        if e["to_Name"] not in Node:
            Node.append(e["to_Name"])


def edge_process(node, Node, Edge, sys):
    client = MongoClient(**MONGO_CONNECTION_CONFIG)
    Link = []
    if node not in Edge:
        prisoner_edges = list(
            client[MONGO_DB_NAMES["database"]][MONGO_DB_NAMES["edge"]].find(
                {"from_Name": node}
            )
        )
        if sys:
            filter_sys(prisoner_edges, "刑事")
        Edge[node] = prisoner_edges
    else:
        prisoner_edges = Edge[node]
    for e in prisoner_edges:
        for nj_index, nj in enumerate(Node):
            # print(f"{nj_index=} {node=}")
            if e["to_Name"] == nj:
                Link.append(
                    {
                        "source": Node.index(e["from_Name"]),
                        "target": Node.index(e["to_Name"]),
                        "weight": e["weight"],
                        "v_id": e["v_id"],
                        "reason": e["reason"],
                        "sys": e["sys"],
                        "court": e["court"],
                        "type": e["type"],
                        "no": e["no"],
                        "date": e["date"],
                    }
                )
    return Link


def get_edge(Node, Edge, Link, sys):  # 取得所有node的edge
    """
    Query all edges connect from node in `Node`, and store to Link.
    """
    # print(f"{mp.cpu_count()=}")
    pool = mp.Pool()
    result = []
    for node_index, node in enumerate(Node):
        # print(f"{node_index=}")
        p = pool.apply_async(edge_process, args=(node, Node, Edge, sys))
        result.append(p)
    for r in result:
        Link += r.get()
    pool.close()
    pool.join()
