"""
Utilities for testing tests
"""
import difflib
from pprint import pformat
import operator
import re

from itertools import repeat, chain, izip

from twisted.trial import unittest
from twisted.test.proto_helpers import StringTransport

from ..server import d20session, session, alias
from ..server.irc import VellumTalk
from .. import user


# FIXME - not needed in python 2.6
def izip_longest(*args, **kwds):
    # izip_longest('ABCD', 'xy', fillvalue='-') --> Ax By C- D-
    fillvalue = kwds.get('fillvalue')
    def sentinel(counter = ([fillvalue]*(len(args)-1)).pop):
        yield counter()         # yields the fillvalue, or raises IndexError
    fillers = repeat(fillvalue)
    iters = [chain(it, sentinel(), fillers) for it in args]
    try:
        for tup in izip(*iters):
            yield tup
    except IndexError:
        pass


class DiffTestCaseMixin(object):

    def getDiffMsg(self, first, second,
                     fromfile='First', tofile='Second'):
        """Return a unified diff between first and second."""
        # Force inputs to iterables for diffing.
        # use pformat instead of str or repr to output dicts and such
        # in a stable order for comparison.
        diff = difflib.unified_diff(
            first, second, fromfile=fromfile, tofile=tofile)
        # Add line endings.
        return '\n' + ''.join([d + '\n' for d in diff])

    def getFormattedVersions(self, first, second, formatter=None):
        if formatter is not None:
            return formatter(first, second)

        if isinstance(first, (tuple, list, dict)):
            first = [pformat(d) for d in first]
        else:
            first = [pformat(first)]

        if isinstance(second, (tuple, list, dict)):
            second = [pformat(d) for d in second]
        else:
            second = [pformat(second)]

        return first, second


    def failIfDiff(self, first, second, fromfile='First', tofile='Second',
            eq=operator.eq, formatter=None):
        """
        If not eq(first, second), fail with a unified diff.
        """
        if not eq(first, second):
            first, second = self.getFormattedVersions(first, second, formatter)

            msg = self.getDiffMsg(first, second, fromfile, tofile)
            raise self.failureException, msg

    assertNoDiff = failIfDiff

    def failIfRxDiff(self, first, second, fromfile='First', tofile='Second'):
        """
        Do the equality comparison using regular expression matching, using
        the first argument as the expression to match against the second
        expression.
        """
        assert type(first) is type(second) is list
        marks = {}

        # pad them
        ff = []
        ss = []
        for f, s in izip_longest(first, second, fillvalue='~~MISSING~~'):
            ff.append(f)
            ss.append(s)

        first = ff
        second = ss

        def eq(first, second):
            if len(first) != len(second):
                return False
            for n, (f, s) in enumerate(zip(first, second)):
                if re.match(f, s) is None:
                    marks[n] = f
            return len(marks) == 0

        def fmt(first, second, marks):
            l1 = []
            l2 = second
            for n, (f, s) in enumerate(zip(first, second)):
                if n not in marks:
                    l1.append(s)
                else:
                    l1.append(f)
            return l1, l2

        self.failIfDiff(first, second, fromfile, tofile, eq=eq,
                formatter=lambda ff, ss: fmt(ff, ss, marks)
                )

    assertNoRxDiff = failIfRxDiff


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

