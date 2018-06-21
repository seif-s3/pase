import numpy as np
import pandas as pd
import matplotlib as plt
import datetime


def add_timestamps(data, output, start_at, delta='1 week'):
    out = open(output, 'w')
    t = datetime.strptime(start_at, '%Y-%m-%d %H:%M:%S')
    out.write("timestamp, value\n")
    for s in data:
        for v in s:
            t += datetime.timedelta(hours=1)
            out.write("{}, {}\n".format(t, v))
    out.close()


def load_instana_data():
    def date_parser(dates):
        return pd.datetime.strptime(dates, '%Y-%m-%d %H:%M:%S')
    data = pd.read_csv('../datasets/instana-with-timestamps.csv',
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