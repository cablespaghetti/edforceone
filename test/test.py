#!/usr/bin/env python3
import os
from mock import patch, mock
from edforceone import run
import unittest
from io import StringIO

class TestCheckStoredGUFI(unittest.TestCase):
    @patch('os.path.isfile', return_value=True)
    @patch('edforceone.run.get_source_xml', return_value="<xml></xml>")
    @patch('os.remove', return_value=False)
    def test_stored_working(self, *args):
        with mock.patch("builtins.open", return_value=StringIO("mockgufi")):
            gufi = run.check_stored_gufi()
            self.assertEqual(gufi, "mockgufi")

    @patch('os.path.isfile', return_value=False)
    @patch('os.remove', return_value=True)
    def test_no_stored(self, *args):
        gufi = run.check_stored_gufi()
        self.assertEqual(gufi, None)

    @patch('os.path.isfile', return_value=True)
    @patch('os.remove', return_value=True)
    @patch('edforceone.run.get_source_xml', return_value=None)
    def test_stored_garbage(self, *args):
        with mock.patch("builtins.open", return_value=StringIO("blergh")):
            gufi = run.check_stored_gufi()
            self.assertEqual(gufi, None)

    @patch('os.path.isfile', return_value=True)
    @patch('edforceone.run.get_source_xml', return_value=None)
    @patch('os.remove', return_value=True)
    def test_stored_not_working(self, *args):
        with mock.patch("builtins.open", return_value=StringIO("mockgufi")):
            gufi = run.check_stored_gufi()
            self.assertEqual(gufi, None)


if __name__ == '__main__':
    unittest.main()




