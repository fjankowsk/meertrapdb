# Copyright (c) 2016 National Research Foundation (South African Radio Astronomy Observatory)
# BSD license - see LICENSE for details
"""Simple example demonstrating sensor information and history queries.

This example gets lists of sensor names in various ways, and gets the
detailed atttributes of a specific sensor.  It also gets the time history
samples for a few sensors.
"""

import argparse
from datetime import datetime
import logging
import time

from katportalclient import KATPortalClient
import tornado.gen


logger = logging.getLogger('katportalclient.example')


@tornado.gen.coroutine
def main():
    # Change URL to point to a valid portal node.
    # If you are not interested in any subarray specific information
    # (e.g. schedule blocks), then the number can be omitted, as below.
    # Note: if on_update_callback is set to None, then we cannot use the
    #       KATPortalClient.connect() and subscribe() methods here.
    portal_client = KATPortalClient(
        'http://{host}/api/client'.format(**vars(args)),
        on_update_callback=None,
        logger=logger
    )

    # Get the names of sensors matching the patterns
    sensor_names = yield portal_client.sensor_names(args.sensors)
    print("\nMatching sensor names: {}".format(sensor_names))

    # Fetch the details for the sensors found.
    for sensor_name in sensor_names:
        sensor_detail = yield portal_client.sensor_detail(sensor_name)
        print("\nDetail for sensor {}:".format(sensor_name))
        for key in sorted(sensor_detail):
            print("    {}: {}".format(key, sensor_detail[key]))

    num_sensors = len(sensor_names)
    if num_sensors == 0:
        print("\nNo matching sensors found - no history to request!")
    else:
        print("\nRequesting history for {} sensors, from {} to {}"
               .format(
                   num_sensors,
                   datetime.utcfromtimestamp(args.start).strftime('%Y-%m-%dT%H:%M:%SZ'),
                   datetime.utcfromtimestamp(args.end).strftime('%Y-%m-%dT%H:%M:%SZ')
                )
        )

        if len(sensor_names) == 1:
            # Request history for just a single sensor - result is
            # sample_time, value, status
            #    If value timestamp is also required, then add the additional argument:
            #        include_value_time=True
            #    result is then sample_time, value_time, value, status
            history = yield portal_client.sensor_history(
                sensor_names[0],
                args.start, args.end,
                include_value_ts=args.include_value_time
            )
            histories = {sensor_names[0]: history}

        else:
            # Request history for all the sensors - result is sample_time, value, status
            #    If value timestamp is also required, then add the additional argument:
            #        include_value_time=True
            #    result is then sample_time, value_time, value, status
            histories = yield portal_client.sensors_histories(
                sensor_names,
                args.start,
                args.end,
                include_value_ts=args.include_value_time
            )

        print("Found {} sensors.".format(len(histories)))
        for sensor_name, history in list(histories.items()):
            num_samples = len(history)
            print("History for: {} ({} samples)".format(sensor_name, num_samples))
            if num_samples > 0:
                filename = '{0}_{1}_{2}.csv'.format(
                    sensor_name,
                    datetime.utcfromtimestamp(args.start).strftime('%Y_%m_%d'),
                    datetime.utcfromtimestamp(args.end).strftime('%Y_%m_%d'),
                )
                print('Writing to file: {0}'.format(filename))

                with open(filename, 'w') as fd:
                    for idx in range(0, num_samples, args.decimate):
                        item = history[idx]
                        if idx == 0:
                            fd.write('# sensor_name, sample_time, value_time, status, """value"""\n')
                        else:
                            fd.write('{0},{1},{2},{3},"""{4}"""\n'.format(
                                sensor_name,
                                item.sample_time,
                                item.value_time,
                                item.status,
                                item.value
                                )
                            )

                # print to stdout
                for idx in range(0, num_samples, args.decimate):
                    item = history[idx]

                    if idx == 0:
                        print('\t# sensor_name, sample_time, value_time, status, """value"""')
                    else:
                        print('\t{0},{1},{2},{3},"""{4}"""'.format(
                            sensor_name,
                            item.sample_time,
                            item.value_time,
                            item.status,
                            item.value
                            )
                        )


if __name__ == '__main__':
    default_sensors = [
        'fbfuse_1_fbfmc_array_1_phase_reference',
        'fbfuse_1_fbfmc_array_2_phase_reference',
        'fbfuse_2_fbfmc_array_1_phase_reference',
        'fbfuse_2_fbfmc_array_2_phase_reference',
        'fbfuse_1_fbfmc_array_1_centre_frequency',
        'fbfuse_1_fbfmc_array_2_centre_frequency',
        'fbfuse_2_fbfmc_array_1_centre_frequency',
        'fbfuse_2_fbfmc_array_2_centre_frequency'
    ]

    parser = argparse.ArgumentParser(
        description='Download sensor history data.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--host',
        default='10.97.1.14',
        help="hostname or IP of the portal server."
    )

    parser.add_argument(
        '-s', '--start',
        default=time.time() - 3600,
        type=int,
        help="start time of sample query [sec since UNIX epoch]"
    )

    parser.add_argument(
        '-e', '--end',
        type=int,
        default=time.time(),
        help="end time of sample query [sec since UNIX epoch]"
    )

    parser.add_argument(
        '-d', '--decimate',
        type=int,
        metavar='N',
        default=1,
        help="decimation level - only every Nth sample is output."
    )

    parser.add_argument(
        '--sensors',
        default=default_sensors,
        dest='sensors',
        metavar='sensor',
        nargs='+',
        help="list of sensor names or filter strings to request data for"
    )

    parser.add_argument(
        '-v', '--verbose',
        dest='verbose',
        action="store_true",
        default=False,
        help="provide extremely verbose output"
    )

    parser.add_argument(
        '-i', '--include-value-time',
        dest="include_value_time",
        action="store_true",
        help="include value timestamp"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    # Start up the tornado IO loop.
    # Only a single function to run once, so use run_sync() instead of start()
    io_loop = tornado.ioloop.IOLoop.current()
    io_loop.run_sync(main)
