#!/usr/bin/env python
# coding: utf-8

import json
import os
from multiprocessing import Pool

from pymongo import MongoClient

MONGO_IP = os.environ.get("MONGO_IP")
MONGO_PORT = int(os.environ.get("MONGO_PORT"))
MONGO_USERNAME = os.environ.get("MONGO_USERNAME")
MONGO_PASSWORD = os.environ.get("MONGO_PASSWORD")
DATABASE_NAME = os.environ.get("DATABASE_NAME")
VERDICT_COLLECTION_NAME = os.environ.get("VERDICT_COLLECTION_NAME")
NODE_COLLECTION_NAME = os.environ.get("NODE_COLLECTION_NAME")
EDGE_COLLECTION_NAME = os.environ.get("EDGE_COLLECTION_NAME")
FILE_ROOT = "/raw-data"


def load_and_dump(filepath):
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    client = MongoClient(
        host=MONGO_IP,
        port=MONGO_PORT,
        username=MONGO_USERNAME,
        password=MONGO_PASSWORD,
    )
    client[DATABASE_NAME][VERDICT_COLLECTION_NAME].insert_one(data)


if __name__ == "__main__":
    with Pool(16) as pool:
        for dirname in os.listdir(FILE_ROOT):
            dirpath = os.path.join(FILE_ROOT, dirname)
            for file in os.listdir(dirpath):
                filepath = os.path.join(dirpath, file)
                pool.apply_async(
                    load_and_dump, args=(filepath,), error_callback=lambda e: print(e)
                )
        pool.close()
        pool.join()
