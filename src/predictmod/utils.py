import json
import numpy as np
import pandas as pd
import pytz
import matplotlib as plt
import datetime
import decimal
import uuid
from os import listdir
from os.path import isfile, join
from bson.dbref import DBRef
from bson.objectid import ObjectId
from predictmod.app import app


class MongoEncoder(json.JSONEncoder):
    """Class to encode Mongo Document to a JSON friendly string."""

    def default(self, value, **kwargs):
        if isinstance(value, ObjectId):
            return str(value)
        if isinstance(value, DBRef):
            return value.id
        if isinstance(value, datetime.datetime):
            # Append a Z to the parsed datetime
            return value.isoformat() + 'Z'
        if isinstance(value, datetime.date):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, decimal.Decimal):
            return str(value)
        return super(MongoEncoder, self).default(value, **kwargs)


def add_timestamps(data, output, start_at, delta='1 week'):
    out = open(output, 'w')
    t = datetime.strptime(start_at, '%Y-%m-%d %H:%M:%S')
    out.write("timestamp, value\n")
    for s in data:
        for v in s:
            t += datetime.timedelta(hours=1)
            out.write("{}, {}\n".format(t, v))
    out.close()


def get_datasets():
    return [
        f for f in listdir(
            app.config['UPLOAD_FOLDER']) if isfile(join(app.config['UPLOAD_FOLDER'], f))
    ]


def get_series(data, index):
    return data.loc[data['series'] == index].drop('series', axis=1)


def load_instana_data():
    def date_parser(dates):
        return pd.datetime.strptime(dates, '%Y-%m-%dT%H:%M:%SZ')
    data = pd.read_csv('/datasets/instana-with-timestamps.csv',
                       parse_dates=['timestamp'], index_col='timestamp', date_parser=date_parser)
    return data


def plot_week(data, start_day):
    start = datetime.strptime(start_day, '%Y-%m-%d')
    end = start + datetime.timedelta(days=7)
    plt.plot(data[start:end])
    plt.show()


def plot_month(data, start_day):
    start = datetime.strptime(start_day, '%Y-%m-%d')
    end = start + datetime.timedelta(days=30)
    plt.plot(data[start:end])
    plt.show()


def plot_series(data, index):
    series = data.loc[data['series'] == index].drop('series', axis=1)
    plt.plot(series)
    plt.show()


def utcnow():
    """Returns the current UTC datetime. For easy replacement during testing."""
    return datetime.datetime.now(pytz.utc)


def generate_uuid():
    return str(uuid.uuid1())


def get_time_difference(t1, t2):
    """Return the differece in hours between two string timestamp as an integer."""
    FMT = '%Y-%m-%dT%H:%M:%SZ'
    delta = (datetime.datetime.strptime(t2, FMT) - datetime.datetime.strptime(t1, FMT))
    return int(delta.total_seconds() / 60.0 / 60.0)
