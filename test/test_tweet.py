#!/usr/bin/env python3
import os
from mock import patch, mock
from edforceone import run
import unittest
from io import StringIO
import datetime

class TestTweet(unittest.TestCase):

    def test_cycle(self, *args):
        tweet_store = open("tweets.txt", "w")
        tweet_store.write("\n")
        tweet_store.close()
        event_dict = {"departure_actual": None, "departure_estimated": datetime.datetime.strptime("2016-04-17T17:30:00", "%Y-%m-%dT%H:%M:%S"), "arrival_actual": None, "arrival_estimated": datetime.datetime.strptime("2016-04-17T18:30:00", "%Y-%m-%dT%H:%M:%S"), "arr_aerodrome": "EGCC", "dep_aerodrome": "EGPD", "last_pos_time": None}
        tweet = run.tweet(event_dict, "ABD666", False)
        self.assertEqual(tweet, "ABD666 is scheduled to depart from Aberdeen (EGPD) at 17:30:00 UTC. #EdForceOne")
        tweet = run.tweet(event_dict, "ABD666", False)
        self.assertEqual(tweet, "Duplicate")
        event_dict = {"departure_actual": datetime.datetime.strptime("2016-04-17T17:35:00", "%Y-%m-%dT%H:%M:%S"), "departure_estimated": datetime.datetime.strptime("2016-04-17T17:30:00", "%Y-%m-%dT%H:%M:%S"), "arrival_actual": None, "arrival_estimated": datetime.datetime.strptime("2016-04-17T18:35:00", "%Y-%m-%dT%H:%M:%S"), "arr_aerodrome": "EGCC", "dep_aerodrome": "EGPD", "last_pos_time": None}
        tweet = run.tweet(event_dict, "ABD666", False)
        self.assertEqual(tweet, "ABD666 departed from Aberdeen (EGPD) at 17:35:00 UTC. It should arrive in Manchester (EGCC) at 18:35:00 UTC. #EdForceOne")
        tweet = run.tweet(event_dict, "ABD666", False)
        self.assertEqual(tweet, "Duplicate")
        event_dict = {"departure_actual": datetime.datetime.strptime("2016-04-17T17:30:00", "%Y-%m-%dT%H:%M:%S"), "departure_estimated": datetime.datetime.strptime("2016-04-17T17:30:00", "%Y-%m-%dT%H:%M:%S"), "arrival_actual": None, "arrival_estimated": datetime.datetime.strptime("2016-04-17T18:35:00", "%Y-%m-%dT%H:%M:%S"), "arr_aerodrome": "EGCC", "dep_aerodrome": "EGPD", "last_pos_time": None}
        tweet = run.tweet(event_dict, "ABD666", False)
        self.assertEqual(tweet, "Duplicate")
        event_dict = {"departure_actual": datetime.datetime.strptime("2016-04-17T17:35:00", "%Y-%m-%dT%H:%M:%S"), "departure_estimated": datetime.datetime.strptime("2016-04-17T17:30:00", "%Y-%m-%dT%H:%M:%S"), "arrival_actual": datetime.datetime.strptime("2016-04-17T18:40:00", "%Y-%m-%dT%H:%M:%S"), "arrival_estimated": datetime.datetime.strptime("2016-04-17T18:35:00", "%Y-%m-%dT%H:%M:%S"), "arr_aerodrome": "EGCC", "dep_aerodrome": "EGPD", "last_pos_time": None}
        tweet = run.tweet(event_dict, "ABD666", False)
        self.assertEqual(tweet, "ABD666 has landed in Manchester (EGCC). #EdForceOne")
        tweet = run.tweet(event_dict, "ABD666", False)
        self.assertEqual(tweet, "Duplicate")

if __name__ == '__main__':
    unittest.main()

