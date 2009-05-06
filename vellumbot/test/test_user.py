"""
Test user
"""
from vellumbot import user

from twisted.trial import unittest

class UserTestCase(unittest.TestCase):
    def test_parseURI(self):
        """
        Parse URI can parse either sqlite: or non-sqlite: strings and returns
        2 strings
        """
        self.assertEqual(user.parseURI('foo.db'), ('foo.db', 'sqlite:foo.db', ))
        self.assertEqual(user.parseURI('sqlite:foo.db'), ('foo.db', 'sqlite:foo.db', ))

