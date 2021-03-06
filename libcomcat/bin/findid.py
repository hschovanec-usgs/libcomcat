#!/usr/bin/env python

# stdlib
import argparse
import sys
import logging
import os.path

# third party
import pandas as pd

# local imports
import libcomcat
from libcomcat.utils import maketime
from libcomcat.dataframes import find_nearby_events
from libcomcat.logging import setup_logger

# constants
TIMEFMT = '%Y-%m-%dT%H:%M:%S'
FILETIMEFMT = '%Y-%m-%d %H:%M:%S'
SEARCH_RADIUS = 100
TIME_WINDOW = 16  # seconds

pd.set_option('display.width', 200)
pd.set_option('display.max_colwidth', 100)


def get_parser():
    desc = '''Find the id(s) of the closest earthquake to input parameters.

    To print the authoritative id of the event closest in time and space
    inside a 100 km, 16 second window to
    "2019-07-15T10:39:32 35.932 -117.715":

    %(prog)s  2019-07-15T10:39:32 35.932 -117.715

    To print the ComCat url of that nearest event:

    %(prog)s  2019-07-15T10:39:32 35.932 -117.715 -u

    To print all of the information about that event:

    %(prog)s  2019-07-15T10:39:32 35.932 -117.715 -v

    To print all of the events that are within expanded distance/time windows:

    %(prog)s  2019-07-15T10:39:32 35.932 -117.715 -a -r 200 -w 120

    To write the output from the last command into a spreadsheet:

    %(prog)s  2019-07-15T10:39:32 35.932 -117.715 -a -r 200 -w 120 -o
    '''

    parser = argparse.ArgumentParser(
        description=desc, formatter_class=argparse.RawDescriptionHelpFormatter)
    # positional arguments
    thelp = ('Time of earthquake, formatted as YYYY-mm-dd or '
             'YYYY-mm-ddTHH:MM:SS')
    parser.add_argument('time', type=maketime,
                        help=thelp)
    parser.add_argument('lat', type=float, help='Latitude of earthquake')
    parser.add_argument('lon', type=float, help='Longitude of earthquake')

    # optional arguments
    parser.add_argument('--version', action='version',
                        version=libcomcat.__version__)
    rhelp = 'Change search radius from default of %.0f km.' % SEARCH_RADIUS
    parser.add_argument('-r', '--radius', type=float,
                        help=rhelp)
    whelp = 'Change time window of %.0f seconds.' % TIME_WINDOW
    parser.add_argument('-w', '--window', type=float,
                        help=whelp)
    parser.add_argument('-a', '--all', dest='print_all', action='store_true',
                        help='Print all ids associated with event.',
                        default=False)
    parser.add_argument('-u', '--url', dest='print_url', action='store_true',
                        help='Print URL associated with event.', default=False)
    vstr = ('Print time/distance deltas, and azimuth from input '
            'parameters to event.')
    parser.add_argument('-v', '--verbose', dest='print_verbose',
                        action='store_true', help=vstr, default=False)
    ohelp = ('Send -a output to a file. Supported formats are Excel and CSV, '
             'format will be determined by extension (.xlsx and .csv)')
    parser.add_argument('-o', '--outfile',
                        help=ohelp)

    loghelp = '''Send debugging, informational, warning and error messages to a file.
    '''
    parser.add_argument('--logfile', default='stderr', help=loghelp)
    levelhelp = '''Set the minimum logging level. The logging levels are (low to high):

     - debug: Debugging message will be printed, most likely for developers.
              Most verbose.
     - info: Only informational messages, warnings, and errors will be printed.
     - warning: Only warnings (i.e., could not retrieve information for a
                single event out of many) and errors will be printed.
     - error: Only errors will be printed, after which program will stop.
              Least verbose.
    '''
    parser.add_argument('--loglevel', default='info',
                        choices=['debug', 'info', 'warning', 'error'],
                        help=levelhelp)
    return parser


def main():
    # set the display width such that table output is not truncated
    pd.set_option('display.max_columns', 10000)
    pd.set_option("display.max_colwidth", 10000)
    pd.set_option("display.expand_frame_repr", False)

    parser = get_parser()

    args = parser.parse_args()

    # trap for mutually exclusive options a, u and v
    argsum = (args.print_all + args.print_url + args.print_verbose)
    if argsum > 1:
        msg = ('The -a, -v, and -u options are mutually exclusive. '
               'Choose one of these options. Exiting.')
        print(msg)
        sys.exit(1)

    # if -o option you must have specified -a option also
    if args.outfile is not None and not args.print_all:
        print('You must select -a and -o together. Exiting')
        sys.exit(1)

    # if -o format is not recognized, error out
    if args.outfile is not None:
        fpath, fext = os.path.splitext(args.outfile)
        supported = ['.xlsx', '.csv']
        if fext not in supported:
            fmt = ('File extension %s not in list of supported '
                   'formats: %s. Exiting.')
            print(fmt % (fext, str(supported)))
            sys.exit(1)

    setup_logger(args.logfile, args.loglevel)

    twindow = TIME_WINDOW
    if args.window:
        twindow = args.window
    # set distance thresholds
    radius = SEARCH_RADIUS
    if args.radius:
        radius = args.radius

    event_df = find_nearby_events(args.time, args.lat,
                                  args.lon, twindow, radius)

    if event_df is None:
        logging.error(
            'No events found matching your search criteria. Exiting.')
        sys.exit(0)

    nearest = event_df.iloc[0]

    if args.print_all:
        if not args.outfile:
            print(event_df)
        else:
            fpath, fext = os.path.splitext(args.outfile)
            if fext == '.xlsx':
                event_df.to_excel(args.outfile, index=False)
            else:
                event_df.to_csv(args.outfile, index=False)
            print('Wrote %i records to %s' % (len(event_df), args.outfile))
        sys.exit(0)

    if args.print_verbose:
        print('Event %s' % nearest['id'])
        cols = nearest.index.to_list()
        cols.remove('id')
        for col in cols:
            print('  %s : %s' % (col, nearest[col]))
        sys.exit(0)

    if args.print_url:
        print(nearest['url'])
        sys.exit(0)

    print(nearest['id'].values[0])


if __name__ == '__main__':
    main()
