#!/usr/bin/env python3
import os
from mock import patch
from edforceone import run
import unittest

class TestCheckStoredGUFI(unittest.TestCase):
    def test_no_stored(self):
        gufi = run.check_stored_gufi()
        self.assertEqual(gufi, None)

if __name__ == '__main__':
    unittest.main()




