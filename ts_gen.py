import argparse
import timesynth as ts
from datetime import datetime, timedelta


def makeParser():
    parser = argparse.ArgumentParser(
        description='Generate a timeseries according to a pattern. Redirect output to file to save')
    parser.add_argument(
        '-func', help='Specify a function to ping according to')
    parser.add_argument('-start', help='Start time in format YYYY-MM-DDTHH:mm:ssZ')
    parser.add_argument('-steps', help='Number of samples to generate')
    parser.add_argument('-g', help='Granularity: default is hours')
    return parser


def ar(steps, scale):
    # Initializing TimeSampler
    steps = int(steps)
    time_sampler = ts.TimeSampler(stop_time=steps)
    # Sampling regular time samples
    regular_time_samples = time_sampler.sample_regular_time(num_points=steps)

    # Initializing AR(2) model
    ar_p = ts.signals.AutoRegressive(ar_param=[1.5, -0.75])
    ar_p_series = ts.TimeSeries(signal_generator=ar_p)
    samples = ar_p_series.sample(regular_time_samples)
    return samples[0]


def main():
    args = makeParser().parse_args()
    try:
        start = datetime.strptime(args.start, '%Y-%m-%dT%H:%M:%SZ')
    except:
        print("Cannot parse start date. Must be in format %Y-%m-%dT%H:%M:%SZ")

    if args.func == 'ar':
        samples = ar(args.steps, args.scale)

    t = start
    print("timestamp,value")
    for s in samples:
        print("{},{}".format(t, s))
        t += timedelta(hours=1)


if __name__ == '__main__':
    main()
