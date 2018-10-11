import json
import pandas as pd
from bson.objectid import ObjectId
from predictmod.app import mongo
from predictmod.utils import MongoEncoder, utcnow


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


def get_all_subscribers():
    # Returns a Subscriber as a JSON doc
    query_result = mongo.db.subscribers.find()
    encoder = MongoEncoder()
    docs = [json.loads(encoder.encode(doc)) for doc in query_result]
    return docs


def get_subscriber_by_id(sub_id):
    # Returns a Subscriber as a JSON doc
    query_result = mongo.db.subscribers.find_one({'_id': ObjectId(sub_id)})
    encoder = MongoEncoder()
    return json.loads(encoder.encode(query_result))


def update_subscriber_predictions(sub_id, pred_id):
    query_result = mongo.db.subscribers.find_one_and_update(
        {'_id': ObjectId(sub_id)},
        {
            "$set":
                {
                    "predictions": get_predictions_by_id(pred_id)
                }
        }
    )
    if query_result:
        return True
    return False


def get_predictions_by_id(pred_id):
    # Returns a Prediction as a JSON doc
    query_result = mongo.db.predictions.find_one({'_id': ObjectId(pred_id)})
    encoder = MongoEncoder()
    return json.loads(encoder.encode(query_result))


def save_predictions(obj):
    inserted = mongo.db.predictions.insert_one(obj)
    encoder = MongoEncoder()
    return encoder.encode(inserted.inserted_id)


def invalidate_predictions(pred_id):
    # Returns a Prediction as a JSON doc
    query_result = mongo.db.predictions.find_one_and_update(
        {'_id': ObjectId(pred_id)},
        {
            '$set': {"is_valid": False, "invalidated_at": utcnow()}
        }
    )
    encoder = MongoEncoder()
    return json.loads(encoder.encode(query_result))


def update_model_input(model_id, input_end):
    query_result = mongo.db.models.find_one_and_update(
        {'_id': ObjectId(model_id)},
        {
            "$set":
                {
                    "input_end": pd.datetime.strptime(input_end, '%Y-%m-%dT%H:%M:%SZ'),
                    "acquisition_time": utcnow(),
                    "input_source": "influx"
                }
        }
    )
    if query_result:
        return True
    return False
