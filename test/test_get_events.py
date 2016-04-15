#!/usr/bin/env python3
import os
from mock import patch, mock
from edforceone import run
import unittest
from io import StringIO
import datetime

class TestGetEvents(unittest.TestCase):
    def test_scheduled(self, *args):
        scheduled_file = open("test/flight_scheduled.xml", "r")
        scheduled_xml = scheduled_file.read()
        events = run.get_events(scheduled_xml)
        expected_result = {"departure_actual": None, "departure_estimated": datetime.datetime.strptime("2016-04-17T17:30:00", "%Y-%m-%dT%H:%M:%S"), "arrival_actual": None, "arrival_estimated": datetime.datetime.strptime("2016-04-17T18:30:00", "%Y-%m-%dT%H:%M:%S"),
            "arr_aerodrome": "EGCC", "dep_aerodrome": "EGPD", "last_pos_time": None}
        self.assertEqual(expected_result, events)
        scheduled_file.close()

    def test_airborne(self, *args):
        airborne_file = open("test/flight_airborne.xml", "r")
        airborne_xml = airborne_file.read()
        events = run.get_events(airborne_xml)
        expected_result = {"departure_actual": datetime.datetime.strptime("2016-04-15T11:55:00", "%Y-%m-%dT%H:%M:%S"), "departure_estimated": datetime.datetime.strptime("2016-04-15T12:11:34", "%Y-%m-%dT%H:%M:%S"), "arrival_actual": None, "arrival_estimated": datetime.datetime.strptime("2016-04-15T13:06:34", "%Y-%m-%dT%H:%M:%S"),
            "arr_aerodrome": "EGAC", "dep_aerodrome": "EGFF", "last_pos_time": datetime.datetime.strptime("2016-04-15T13:01:51", "%Y-%m-%dT%H:%M:%S")}
        self.assertEqual(expected_result, events)
        airborne_file.close()

    def test_garbage(self, *args):
        garbage_file = open("test/flight_garbage.xml", "r")
        garbage_xml = garbage_file.read()
        events = run.get_events(garbage_xml)
        expected_result = {"departure_actual": None, "departure_estimated": None, "arrival_actual": None, "arrival_estimated": None,
              "arr_aerodrome": None, "dep_aerodrome": None, "last_pos_time": None}
        self.assertEqual(expected_result, events)
        garbage_file.close()

if __name__ == '__main__':
    unittest.main()




