import json
import multiprocessing as mp

import networkx as nx
from bson.objectid import ObjectId
from networkx.readwrite.json_graph import node_link_graph
from pymongo import MongoClient

from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt

from .utils import (
    MONGO_CONNECTION_CONFIG,
    MONGO_DB_NAMES,
    get_edge,
    get_node,
    node_process,
)


def homepage(request):
    return redirect("/graph/")


def graph(request):
    template = get_template("graph.html")
    level = ["第1層", "第2層"]
    html = template.render(locals())
    return HttpResponse(html)


@csrf_exempt
def search_prisoner(request):
    # print(f"{request.POST=}")
    prisoner = request.POST["prisoner"]

    client = MongoClient(**MONGO_CONNECTION_CONFIG)
    result = []

    for index, n in enumerate(
        client[MONGO_DB_NAMES["database"]][MONGO_DB_NAMES["node"]].find(
            {"$text": {"$search": prisoner}}, no_cursor_timeout=True
        )
    ):
        if prisoner in n["name"]:
            result.append(n["name"])

    result = {"prisoner": result}
    return JsonResponse(result)


@csrf_exempt
def get_graph_data(request):
    # start = datetime.datetime.now()
    # print("{request.POST=}")
    prisoner = request.POST["prisoner"]
    level = int(request.POST["level"])
    sys = str(request.POST["sys"])

    Node = []  # Graph node
    Link = []  # Graph edge
    Target = [prisoner]  # 現在level要找的node
    haveFindNode = []  # 曾經找過的node
    Edge = {}  # 所有node的edge
    Map = []

    for _ in range(level):
        for t in Target:
            get_node(t, Node, Edge, sys)
            haveFindNode.append(t)
        Target = []
        for n in Node:  # target為新增的node中 不曾找過的node
            if n not in haveFindNode:  # 曾經找過node 不再是下次target
                Target.append(n)

    # Get all edge
    get_edge(Node, Edge, Link, sys)

    # Get node information
    pool = mp.Pool()
    Node_result = []
    for n in Node:
        # print("{n=}")
        p = pool.apply_async(node_process, args=(n,))
        Node_result.append(p)
    for r in Node_result:
        Map.append(r.get())
    pool.close()
    pool.join()

    result = {"Map": Map, "Link": Link}
    # time = datetime.datetime.now() - start
    # print(f"{time=}")
    return JsonResponse(result)


@csrf_exempt
def get_shortest_path(request):
    source = request.POST["source"]
    target = request.POST["target"]
    # print(f"{os.getcwd()=}")
    # print(f"{source=}, {target=}")
    client = MongoClient(**MONGO_CONNECTION_CONFIG)
    with open("static/graph/Law_edge_gragh.json", "r", encoding="UTF-8") as F:
        G = node_link_graph(json.load(F))

    Node = []
    Link = []
    Map = []
    try:
        path = nx.shortest_path(G, source=source, target=target)
        # print(f"{path=}")
        for ni, n in enumerate(path):
            Node.append(n)
            if ni != len(path) - 1:
                this_Edge = list(
                    client[MONGO_DB_NAMES["database"]][MONGO_DB_NAMES["edge"]].find(
                        {"from_Name": n, "to_Name": path[ni + 1]}
                    )
                )[0]
                Link.append(
                    {
                        "source": ni,
                        "target": ni + 1,
                        "weight": this_Edge["weight"],
                        "v_id": this_Edge["v_id"],
                        "reason": this_Edge["reason"],
                        "sys": this_Edge["sys"],
                        "court": this_Edge["court"],
                        "type": this_Edge["type"],
                        "no": this_Edge["no"],
                        "date": this_Edge["date"],
                    }
                )
    except Exception:
        path = []
        Node = [source, target]

    for n in Node:
        try:
            this_Node = client[MONGO_DB_NAMES["database"]][MONGO_DB_NAMES["node"]].find(
                {"name": n}
            )[0]
            this_Node = {
                "name": n,
                "v_id": this_Node["v_id"],
                "reason": this_Node["reason"],
                "sys": this_Node["sys"],
                "court": this_Node["court"],
                "type": this_Node["type"],
                "no": this_Node["no"],
                "date": this_Node["date"],
            }
        except Exception:
            this_Node = {"name": n}
        Map.append(this_Node)
    result = {"Map": Map, "Link": Link}
    return JsonResponse(result)


@csrf_exempt
def get_verdict(request):
    verdict_id = request.POST["verdict"]

    # print("{verdict_id=}")

    client = MongoClient(**MONGO_CONNECTION_CONFIG)
    Verdict = list(
        client[MONGO_DB_NAMES["database"]][MONGO_DB_NAMES["verdict"]].find(
            {"_id": ObjectId(verdict_id)}
        )
    )[0]

    result = {
        "mainText": Verdict["mainText"],
        "court": Verdict["court"],
        "judgement": Verdict["judgement"],
        "no": Verdict["no"],
        "type": Verdict["type"],
        "sys": Verdict["sys"],
        "opinion": Verdict["opinion"],
        "reason": Verdict["reason"],
        "date": Verdict["date"],
    }
    return JsonResponse(result)
