import json
from bson.objectid import ObjectId
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
    # Returns a Model as a JSON doc
    query_result = mongo.db.models.find_one({'_id': ObjectId(model_id)})
    encoder = MongoEncoder()
    return json.loads(encoder.encode(query_result))


def get_subscriber_by_id(sub_id):
    # Returns a Subscriber as a JSON doc
    query_result = mongo.db.subscribers.find_one({'id': sub_id})
    encoder = MongoEncoder()
    return json.loads(encoder.encode(query_result))


def get_predictions_by_id(pred_id):
    # Returns a Prediction as a JSON doc
    query_result = mongo.db.predictions.find_one({'_id': pred_id})
    encoder = MongoEncoder()
    return json.loads(encoder.encode(query_result))
