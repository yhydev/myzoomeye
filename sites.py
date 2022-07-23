import pymongo
import os
import logging
import datetime
_mongo_url = os.environ['MONGO_URL']
_mongo_database = os.environ['MONGO_DATABASE']
_mongo = pymongo.MongoClient(_mongo_url)[_mongo_database]
_sites = _mongo['sites']


def save(params, sites):
    now = datetime.datetime.now()
    _sites.insert_one({
        "params": params,
        "sites":sites,
        "create_datetime": now
    })
    logging.info("sites: [%s]", sites)