#!/usr/bin/env python
# coding: utf-8

import logging
import os
import re
import time
from multiprocessing import Process

from pymongo import MongoClient
from pymongo.errors import AutoReconnect

MONGO_IP = os.environ.get("MONGO_IP")
MONGO_PORT = int(os.environ.get("MONGO_PORT"))
MONGO_USERNAME = os.environ.get("MONGO_USERNAME")
MONGO_PASSWORD = os.environ.get("MONGO_PASSWORD")
DATABASE_NAME = os.environ.get("DATABASE_NAME")
VERDICT_COLLECTION_NAME = os.environ.get("VERDICT_COLLECTION_NAME")
NODE_COLLECTION_NAME = os.environ.get("NODE_COLLECTION_NAME")
EDGE_COLLECTION_NAME = os.environ.get("EDGE_COLLECTION_NAME")
MAX_RETRIES = 5
COLLECTION_NAMES = [VERDICT_COLLECTION_NAME, NODE_COLLECTION_NAME, EDGE_COLLECTION_NAME]
VERDICT_FIELDS = ["reason", "date", "court", "no", "sys", "type"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(message)s")


def handle_mongo_reconnet(func):
    def _wrapped(*args, **kwargs):
        for i in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except AutoReconnect:
                logging.info(f"{os.getpid()}: Retry triggered ({i})")
                time.sleep(pow(2, i))
        logging.info(f"{os.getpid()}: Retry exceed {MAX_RETRIES} times, terminated")

    return _wrapped


def is_valid(name) -> bool:
    # empty name
    if not name:
        return False
    # masked name
    if re.match(r"[\u4e00-\u9fa5]+○+$", name) is not None:
        return False
    return True


def new_context(base, verdict, is_edge=False) -> dict:
    """build new context for person or edge"""
    context = {key: [verdict[key]] for key in VERDICT_FIELDS}
    context.update(base)
    context["v_id"] = [str(verdict["_id"])]
    if is_edge:
        context["weight"] = 1
    return context


def new_edges(source_name, party, verdict):
    edges = []
    for person in party:
        name = person["value"]
        if source_name != name:
            base = {"from_Name": source_name, "to_Name": name}
            edges.append(new_context(base, verdict, is_edge=True))
    return edges


def append_context(client, source_name, context, verdict, is_edge=False):
    for key in VERDICT_FIELDS:
        context[key].append(verdict[key])
    context["v_id"].append(str(verdict["_id"]))

    if is_edge:
        context["weight"] += 1
        collection = client[DATABASE_NAME][EDGE_COLLECTION_NAME]
    else:
        collection = client[DATABASE_NAME][NODE_COLLECTION_NAME]
    handle_mongo_reconnet(collection.find_one_and_replace)(
        {"_id": context["_id"]}, context
    )


def append_edges(client, source_name, party, verdict):
    edge_collection = client[DATABASE_NAME][EDGE_COLLECTION_NAME]
    for person in party:
        name = person["value"]
        if source_name == name:
            continue
        edge = handle_mongo_reconnet(edge_collection.find_one)(
            {"from_Name": source_name, "to_Name": name}
        )

        if edge:
            # 曾經一起出現過
            append_context(client, source_name, edge, verdict, is_edge=True)
        else:
            # 第一次一起出現
            base = {"from_Name": source_name, "to_Name": name}
            handle_mongo_reconnet(edge_collection.insert_one)(
                new_context(base, verdict, is_edge=True)
            )


def extract_person_and_edge(client, verdict, party):
    node_collection = client[DATABASE_NAME][NODE_COLLECTION_NAME]
    edge_collection = client[DATABASE_NAME][EDGE_COLLECTION_NAME]
    for person in party:
        name = person["value"]
        node = handle_mongo_reconnet(node_collection.find_one)({"name": name})
        if node:
            # p已經存在，新增判決書紀錄
            append_context(client, name, node, verdict)
            # 檢查其他重複出現在同一篇判決書的人
            append_edges(client, name, party, verdict)
        else:
            # p第一次出現，建立資料
            handle_mongo_reconnet(node_collection.insert_one)(
                new_context({"name": name}, verdict)
            )

            # 把同一篇出現的人都建立edge
            edges = new_edges(name, party, verdict)
            if edges:
                handle_mongo_reconnet(edge_collection.insert_many)(edges)


def process_verdict(client, verdict):
    valid_party = []
    for party in verdict["party"]:
        if "lawyer" in party["group"]:
            continue
        if "defendant" not in party["group"]:
            continue
        if not is_valid(party["value"]):
            continue
        valid_party.append(party)
    if valid_party:
        extract_person_and_edge(client, verdict, valid_party)
        return True
    return False


def query_and_process():
    client = MongoClient(
        host=MONGO_IP,
        port=MONGO_PORT,
        username=MONGO_USERNAME,
        password=MONGO_PASSWORD,
    )
    verdict_collection = client[DATABASE_NAME][VERDICT_COLLECTION_NAME]

    processed = 0
    found = 0
    log_stage = 1
    while True:
        verdict = handle_mongo_reconnet(verdict_collection.find_one_and_update)(
            {"processed-third": {"$exists": False}},
            {"$set": {"processed-third": True}},
        )

        if not verdict:
            logging.info(f"{os.getpid()}: processed {found}/{processed}")
            logging.info(f"{os.getpid()}： Nothing left to processed, terminated")
            break

        # Processing
        if process_verdict(client, verdict):
            found += 1
        processed += 1

        # Logging
        if processed > log_stage * 10:
            log_stage *= 10
        if processed % log_stage == 0:
            logging.info(f"{os.getpid()}: processed {found}/{processed}")


if __name__ == "__main__":
    processes = []
    num_process = os.cpu_count()
    for i in range(num_process):
        p = Process(target=query_and_process)
        p.start()
        processes.append(p)
    for p in processes:
        p.join()
