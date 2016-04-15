#!/usr/bin/env python3
import os
from mock import patch, mock
from edforceone import run
import unittest
from io import StringIO
import datetime

class TestTweet(unittest.TestCase):

    def test_scheduled(self, *args):
        tweet_store = open("tweets.txt", "w")
        tweet_store.write("\n")
        tweet_store.close()
        event_dict = {"departure_actual": None, "departure_estimated": datetime.datetime.strptime("2016-04-17T17:30:00", "%Y-%m-%dT%H:%M:%S"), "arrival_actual": None, "arrival_estimated": datetime.datetime.strptime("2016-04-17T18:30:00", "%Y-%m-%dT%H:%M:%S"), "arr_aerodrome": "EGCC", "dep_aerodrome": "EGPD", "last_pos_time": None}
        tweet = run.tweet(event_dict, "ABD666", False)
        self.assertEqual(tweet, "ABD666 is scheduled to depart from Aberdeen (EGPD) at 17:30:00 UTC.")
        tweet = run.tweet(event_dict, "ABD666", False)
        self.assertEqual(tweet, "Duplicate")

if __name__ == '__main__':
    unittest.main()




