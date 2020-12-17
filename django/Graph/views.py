import datetime
import json
import multiprocessing as mp
import os

import networkx as nx
from bson.objectid import ObjectId
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from networkx.readwrite.json_graph import node_link_graph
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


def homepage(request):
    return redirect("/graph/")


def graph(request):
    template = get_template("graph.html")
    level = ["第1層", "第2層"]
    html = template.render(locals())
    return HttpResponse(html)


@csrf_exempt
def search_prisoner(request):
    print(request.POST)
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


@csrf_exempt
def get_graph_data(request):
    start = datetime.datetime.now()
    print(request.POST)
    prisoner = request.POST["prisoner"]
    level = request.POST["level"]

    # global Node, Link, Edge
    Node = []  # Graph node
    Link = []  # Graph edge
    Target = [prisoner]  # 現在level要找的node
    haveFindNode = []  # 曾經找過的node
    Edge = {}  # 所有node的edge
    Map = []

    for _ in range(int(level)):
        for t in Target:
            get_node(t, Node, Edge)
            haveFindNode.append(t)
        Target = []
        for n in Node:  # target為新增的node中 不曾找過的node
            if n not in haveFindNode:  # 曾經找過node 不再是下次target
                Target.append(n)

    # Get all edge
    get_Edge(Node, Edge, Link)

    # Get node information
    pool = mp.Pool()
    Node_result = []
    for n in Node:
        print(n)
        p = pool.apply_async(node_process, args=(n,))
        Node_result.append(p)
    for r in Node_result:
        Map.append(r.get())
    pool.close()
    pool.join()

    result = {"Map": Map, "Link": Link}

    time = datetime.datetime.now() - start
    print("Time:", time)

    return JsonResponse(result)


def get_node(prisoner, Node, Edge):  # 取得所有鄰居node
    client = MongoClient(**MONGO_CONNECTION_CONFIG)
    if prisoner not in Node:
        Node.append(prisoner)
    if prisoner not in Edge:
        this_Edge = list(
            client[MONGO_DB_NAMES["database"]][MONGO_DB_NAMES["edge"]].find(
                {"from_Name": prisoner}
            )
        )
        Edge[prisoner] = this_Edge
    else:
        this_Edge = Edge[prisoner]

    for e in this_Edge:
        if e["to_Name"] not in Node:
            Node.append(e["to_Name"])


def edge_process(ni, Node, Edge):
    client = MongoClient(**MONGO_CONNECTION_CONFIG)
    Link = []
    if ni not in Edge:
        this_Edge = list(
            client[MONGO_DB_NAMES["database"]][MONGO_DB_NAMES["edge"]].find(
                {"from_Name": ni}
            )
        )
        Edge[ni] = this_Edge
    else:
        this_Edge = Edge[ni]
    for e in this_Edge:
        for nj_index, nj in enumerate(Node):
            print("nj_index:", nj_index, "ni", ni)
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


def get_Edge(Node, Edge, Link):  # 取得所有node的edge
    print("cpus: ", mp.cpu_count())
    pool = mp.Pool()
    result = []
    for ni_index, ni in enumerate(Node):
        print("ni_index", ni_index)
        p = pool.apply_async(edge_process, args=(ni, Node, Edge))
        result.append(p)
    for r in result:
        Link += r.get()
    pool.close()
    pool.join()


@csrf_exempt
def get_shortest_path(request):
    source = request.POST["source"]
    target = request.POST["target"]
    print(os.getcwd())
    print(source, target)
    client = MongoClient(**MONGO_CONNECTION_CONFIG)
    with open("static/graph/Law_edge_gragh.json", "r", encoding="UTF-8") as F:
        G = node_link_graph(json.load(F))

    Node = []
    Link = []
    Map = []
    try:
        path = nx.shortest_path(G, source=source, target=target)
        print("path:", path)
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
    except:
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
        except:
            this_Node = {"name": n}
        Map.append(this_Node)
    result = {"Map": Map, "Link": Link}
    return JsonResponse(result)


@csrf_exempt
def get_verdict(request):
    verdict_id = request.POST["verdict"]

    print(verdict_id)

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
