#!/usr/bin/env python3
from mock import patch
from edforceone import run
import unittest

class TestGetGUFI(unittest.TestCase):
    @patch('edforceone.run.check_stored_gufi', return_value="mockgufi")
    def test_stored(self, *args):
        result = run.get_gufi("ABD", "666", "fake")
        self.assertEqual(result, "mockgufi")

if __name__ == '__main__':
    unittest.main()

