"""
Utilities for testing tests
"""
import re

from twisted.trial import unittest
from twisted.test.proto_helpers import StringTransport

from ..server import d20session
from ..server.irc import VellumTalk
from .. import user

from playtools.test.util import DiffTestCaseMixin


def formPrivMsg(*recipients):
    if recipients:
        r = ["PRIVMSG %s :%s" % (targ,exp) for targ,exp in recipients]
        return "\n".join(r)
    return ''


NL = re.compile(r'\r?\n')

class ResponseTest:
    """Notation for testing a response to a command."""
    def __init__(self, transport, user, channel, sent, *recipients):
        self.user = user
        self.transport = transport
        self.channel = channel
        self.sent = sent

        self.expectation = formPrivMsg(*recipients)

        self.last_pos = 0

    def getActual(self):
        """
        Pull the actual data from the pipe
        """
        ret = self.transport.value()[self.last_pos:].strip()
        # wipe the text every time.
        self.transport.clear()
        self.last_pos = len(ret)
        return ret

    def check(self, testcase):
        actual = self.getActual()
        # sort the messages because we usually don't care about order (TODO -
        # maybe someday we will)
        actuality = NL.split(actual)
        expectation = NL.split(self.expectation)
        testcase.failIfRxDiff(expectation, actuality,
                        'expected (regex)', 'actual',
                        )
        return True #?


class FakeFactory(object):
    """
    VellumTalk factory proxy, it only holds the store attribute
    """


class BotTestCase(unittest.TestCase, DiffTestCaseMixin):
    """
    Set up a VellumTalk bot, have it join #testing and hide the aliases.
    Tests can be run using the anyone() function
    """
    def setUp(self):
        self.transport = StringTransport()

        vt = self.vt = VellumTalk()
        vt.factory = FakeFactory()
        vt.factory.store = user.userDatabase('sqlite:')
        vt.factory.serverEncoding = 'utf-8'

        vt.performLogin = 0
        vt.defaultSession = vt.factory.store.find(d20session.D20Session,
                d20session.D20Session.name == u'#@@default@@').one()
        vt.defaultSession.isDefaultSession = True
        vt.makeConnection(self.transport)
        vt.joined(u"#testing")

    def addUser(self, name):
        """
        Convenience to add and return a user
        """
        u = user.User()
        u.name = name
        self.vt.store.add(u)
        self.vt.store.commit()
        return u

    def tearDown(self):
        self.vt.resetter.stop()

    def anyone(self, who, channel, target, *recipients):
        """
        Simulate an interaction between the named person and VellumTalk
        """
        r = ResponseTest(self.transport, who, channel, target, *recipients)
        self.vt.privmsg(r.user, r.channel, r.sent)
        r.check(self)

