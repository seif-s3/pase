import argparse
import timesynth as ts
import json as jsonlib
import pprint
from datetime import datetime, timedelta
from scipy.interpolate import interp1d


def makeParser():
    parser = argparse.ArgumentParser(
        description='Generate a timeseries according to a pattern. Redirect output to file to save')
    parser.add_argument(
        '-f', help='Specify a function to ping according to')
    parser.add_argument('-s', help='Start time in format YYYY-MM-DDTHH:mm:ssZ')
    parser.add_argument('-e', help='Start time in format YYYY-MM-DDTHH:mm:ssZ')
    parser.add_argument('-g', help='Granularity, minutes between samples, default 1hr', default=3600, type=int)
    parser.add_argument('-out', help='Granularity: default is hours')
    parser.add_argument('-max', help='Max range for values', type=int)
    parser.add_argument('-min', help='Max range for values', type=int)
    parser.add_argument('-json', help='Output as JSON', action='store_true', default=False)
    return parser.parse_args()


def ar(steps, min, max):
    # Initializing TimeSampler
    time_sampler = ts.TimeSampler(stop_time=steps)
    # Sampling regular time samples
    regular_time_samples = time_sampler.sample_regular_time(num_points=steps)
    # Initializing AR(2) model
    ar_p = ts.signals.AutoRegressive(ar_param=[1.5, -0.75])
    ar_p_series = ts.TimeSeries(signal_generator=ar_p)
    samples, signals, errors = ar_p_series.sample(regular_time_samples)
    interpolator = interp1d([samples.min(), samples.max()], [min, max])
    ret = []
    for s in samples:
        ret.append(int(interpolator(s)))
    return ret


def car(steps, min, max):
    car = ts.signals.CAR(ar_param=0.9, sigma=0.01)
    car_series = ts.TimeSeries(signal_generator=car)
    time_sampler = ts.TimeSampler(stop_time=steps)
    regular_time_samples = time_sampler.sample_regular_time(num_points=steps)
    samples, signals, errors = car_series.sample(regular_time_samples)
    ret = []
    interpolator = interp1d([samples.min(), samples.max()], [min, max])
    for s in samples:
        ret.append(int(interpolator(s)))
    return ret


def gaussian(steps, min, max):
    gp = ts.signals.GaussianProcess(kernel='Matern', nu=3.0/2)
    gp_series = ts.TimeSeries(signal_generator=gp)
    time_sampler = ts.TimeSampler(stop_time=steps)
    regular_time_samples = time_sampler.sample_regular_time(num_points=steps)
    samples = gp_series.sample(regular_time_samples)[0]
    ret = []
    interpolator = interp1d([samples.min(), samples.max()], [min, max])
    for s in samples:
        ret.append(int(interpolator(s)))
    return ret


def output(samples, start, end, g, json=False):
    if json:
        t = start
        arr = []
        for s in samples:
            arr.append({'timestamp': t.strftime('%Y-%m-%dT%H:%M:%SZ'), 'requests': s})
            t += timedelta(seconds=g)
        print(jsonlib.dumps(arr))
    else:
        t = start
        print("timestamp,value")
        for s in samples:
            print("{},{}".format(t.strftime('%Y-%m-%dT%H:%M:%SZ'), s))
            t += timedelta(seconds=g)


def main():
    args = makeParser()
    try:
        start = datetime.strptime(args.s, '%Y-%m-%dT%H:%M:%SZ')
        end = datetime.strptime(args.e, '%Y-%m-%dT%H:%M:%SZ')
        delta = end - start
        steps = (delta.total_seconds() + args.g) / args.g
    except:
        print("Cannot parse start date. Must be in format %Y-%m-%dT%H:%M:%SZ")
        return

    if not args.min or not args.max:
        print("Error: -min and -max are required arguments")
        return

    if args.f == 'ar':
        samples = ar(steps, args.min, args.max)
    elif args.f == 'car':
        samples = car(steps, args.min, args.max)
    elif args.f == 'gaussian':
        samples = gaussian(steps, args.min, args.max)
    else:
        print("Unknown algorithm. Choices are [ar, car, gaussian]")
        return

    output(samples, start, end, args.g, json=args.json)


if __name__ == '__main__':
    main()
