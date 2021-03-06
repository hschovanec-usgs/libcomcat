#!/usr/bin/env python

from datetime import datetime
import os.path

import vcr
from libcomcat.search import search, count, get_event_by_id
from libcomcat.classes import DetailEvent


def get_datadir():
    # where is this script?
    homedir = os.path.dirname(os.path.abspath(__file__))
    datadir = os.path.join(homedir, '..', 'data')
    return datadir


def test_get_event():
    eventid = 'ci3144585'
    datadir = get_datadir()
    tape_file = os.path.join(datadir, 'vcr_event.yaml')
    with vcr.use_cassette(tape_file):
        event = get_event_by_id(eventid)

    assert isinstance(event, DetailEvent)
    assert event.id == eventid
    assert (event.latitude, event.longitude) == (34.213, -118.537)


def test_count():
    datadir = get_datadir()
    tape_file = os.path.join(datadir, 'vcr_count.yaml')
    with vcr.use_cassette(tape_file):
        nevents = count(starttime=datetime(1994, 1, 17, 12, 30),
                        endtime=datetime(1994, 1, 18, 12, 35),
                        minmagnitude=6.6, verbose=True,
                        updatedafter=datetime(2010, 1, 1))
    assert nevents == 1


def test_search():
    datadir = get_datadir()
    tape_file = os.path.join(datadir, 'vcr_search.yaml')
    with vcr.use_cassette(tape_file):
        eventlist = search(starttime=datetime(1994, 1, 17, 12, 30),
                           endtime=datetime(1994, 1, 18, 12, 35),
                           minmagnitude=6.6)
        event = eventlist[0]
        assert event.id == 'ci3144585'

        events = search(minmagnitude=9.0, maxmagnitude=9.9,
                        starttime=datetime(2008, 1, 1),
                        endtime=datetime(2010, 2, 1),
                        updatedafter=datetime(2010, 1, 1))

        events = search(maxmagnitude=0.1,
                        starttime=datetime(2017, 1, 1),
                        endtime=datetime(2017, 1, 30))


if __name__ == '__main__':
    test_get_event()
    test_count()
    test_search()
