import json
from predictmod.app import mongo
from predictmod.utils import MongoEncoder


def get_active_model():
    """Returns the id of the active model or None if there aren't any active models."""
    query_result = mongo.db.active_model.find()
    encoder = MongoEncoder()
    docs = [json.loads(encoder.encode(doc)) for doc in query_result]
    if len(docs) == 1:
        return docs[0]['model_id']
    else:
        return None


def get_model_by_id(model_id):
    query_result = mongo.db.models.find_one({'id': model_id})
    encoder = MongoEncoder()
    return json.loads(encoder.encode(query_result))


def get_subscriber_by_id(sub_id):
    query_result = mongo.db.subscribers.find_one({'id': sub_id})
    encoder = MongoEncoder()
    return json.loads(encoder.encode(query_result))
