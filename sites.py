import pymongo
import os
import logging
import datetime
_mongo_url = os.environ['MONGO_URL']
_mongo_database = os.environ['MONGO_DATABASE']
_mongo = pymongo.MongoClient(_mongo_url)[_mongo_database]
_sites = _mongo['sites']
import json
import hashlib

def __get_hex_md5(value):
    md5 = hashlib.md5()
    md5.update(bytes(value, "utf-8"))
    return md5.hexdigest()

def __get_params_digest(params):
    paramsStr = json.dumps(params,sort_keys=True)
    return __get_hex_md5(paramsStr)

def save(params, sites):
    now = datetime.datetime.now()
    _sites.insert_one({
        "params": params,
        "params_digest": __get_params_digest(params),
        "sites":sites,
        "create_datetime": now
    })

def exists(params):
    digest = __get_params_digest(params)
    return _sites.count_documents({"params_digest": digest})