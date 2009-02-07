import unittest
import re

from twisted.internet import protocol
from twisted.words.test.test_irc import StringIOWithoutClosing

from vellumbot.server import alias, d20session
from vellumbot.server.irc import VellumTalk
import vellumbot.server.session
from . import util

class ResponseTest:
    """Notation for testing a response to a command."""
    def __init__(self, factory, user, channel, sent, *recipients):
        self.user = user
        self.factory = factory
        self.channel = channel
        self.sent = sent

        if len(recipients) == 0:
            self.recipients = None
        else:
            self.recipients = list(recipients)

        self.last_pos = 0

    def check(self, testcase):
        pipe = self.factory.pipe
        pipe.seek(self.factory.pipe_pos)
        actual = pipe.read().strip()
        self.factory.pipe_pos = pipe.tell()
        if self.recipients is None:
            testcase.assertEqual(actual, '')
        else:
            rcpts = sorted(self.recipients)
            expected = ['PRIVMSG %s :%s' % (targ,exp) for targ,exp in rcpts]
            actual = sorted(actual.splitlines())
            testcase.failIfDiff(actual, expected, 'actual', 'expected')
            return
            for _line in actual.splitlines():
                for target, expected in self.recipients:
                    pattern = 'PRIVMSG %s :%s' % (re.escape(target), 
                                                  expected)
                    # remove a recipient each time a line is found
                    # matching a line that was expected
                    if re.match(pattern, _line):
                        self.satisfy(target, expected)
                # pass when there are no recipients left to satisfy
                if len(self.recipients) == 0:
                    return True
            else:
                assert 0, "you fail"
        return True #?

    def satisfy(self, target, expected):
        self.recipients.remove((target, expected))


class ResponseTestFactory:
    def __init__(self, pipe):
        self.pipe = pipe
        self.pipe_pos = 0

    def next(self, user, channel, target, *recipients):
        return ResponseTest(self,
                            user,
                            channel, 
                            target, 
                            *recipients)


class IRCTestCase(unittest.TestCase, util.DiffTestCaseMixin):
    factory = None

    def setUp(self):
        if self.factory is None:
            pipe = StringIOWithoutClosing()
            self.factory = ResponseTestFactory(pipe)

        # TODO - move d20-specific tests, e.g. init and other alias hooks?
        # save off and clear alias.aliases, since it gets persisted # FIXME
        orig_aliases = alias.aliases
        alias.aliases = {}

        transport = protocol.FileWrapper(pipe)
        vt = self.vt = VellumTalk()
        vt.performLogin = 0
        vt.joined("#testing")
        vt.defaultSession = d20session.D20Session('#testing')
        vt.makeConnection(transport)

    def geeEm(self, channel, target, *recipients):
        r = self.factory.next('GeeEm', channel, target, *recipients)
        self.vt.privmsg(r.user, r.channel, r.sent)
        r.check(self)

    def player(self, channel, target, *recipients):
        r = self.factory.next('Player', channel, target, *recipients)
        self.vt.privmsg(r.user, r.channel, r.sent)
        r.check(self)

    def test_everything(self):
        vellumbot.server.session.TESTING = True
        vellumbot.server.irc.TESTING = True
        self.geeEm('VellumTalk', 'hello')
        self.geeEm('VellumTalk', 'OtherGuy: hello')
        self.geeEm('VellumTalk', 'VellumTalk: hello', ('GeeEm', r'Hello GeeEm.'))
        self.geeEm('VellumTalk', 'Vellumtalk: hello there', ('GeeEm', r'Hello GeeEm.'))
        self.geeEm('VellumTalk', '.hello', ('GeeEm', r'Hello GeeEm.'))
        self.geeEm('#testing', 'hello',)
        self.geeEm('#testing', 'VellumTalk: hello', ('#testing', r'Hello GeeEm.'))
        self.geeEm('#testing', '.hello', ('#testing', r'Hello GeeEm.'))
        self.geeEm('VellumTalk', '.inits', ('GeeEm', r'Initiative list: (none)'))
        self.geeEm('VellumTalk', '.combat', ('GeeEm', r'** Beginning combat **'))
        self.geeEm('#testing', '[init 20]', 
              ('#testing', r'GeeEm, you rolled: init 20 = [20]'))
        self.geeEm('VellumTalk', '.n', ('GeeEm', r'++ New round ++'))
        self.geeEm('VellumTalk', '.n', 
              ('GeeEm', r'GeeEm (init 20) is ready to act . . .'))
        self.geeEm('VellumTalk', '.p', ('GeeEm', r'++ New round ++'))
        self.geeEm('VellumTalk', '.p', 
              ('GeeEm', r'GeeEm (init 20) is ready to act . . .'))
        self.geeEm('VellumTalk', '.inits', 
              ('GeeEm', r'Initiative list: GeeEm/20, NEW ROUND/9999'))
        # self.geeEm('VellumTalk', '.help', ('GeeEm', r's+hello: Greet.')), FIXME
        self.geeEm('VellumTalk', '.aliases', ('GeeEm', r'Aliases for GeeEm:   init=20'))
        self.geeEm('VellumTalk', '.aliases GeeEm', 
              ('GeeEm', r'Aliases for GeeEm:   init=20'))
        self.geeEm('VellumTalk', '.aliases GeeEm Player',   
               ('GeeEm', 'Aliases for GeeEm:   init=20'), ('GeeEm', 'Aliases for Player:   (none)'))
        self.geeEm('VellumTalk', '.unalias foobar', 
              ('GeeEm', r'** No alias "foobar" for GeeEm'))
        self.geeEm('#testing',  'hello [argh 20] [foobar 30]', 
              ('#testing', r'GeeEm, you rolled: argh 20 = [20]'),
              ('#testing', r'GeeEm, you rolled: foobar 30 = [30]'))
        self.geeEm('#testing',  '[argh +1]', 
              ('#testing', r'GeeEm, you rolled: argh +1 = [20+1 = 21]'))
        self.geeEm('#testing',  'I will [kill 20] them @all', 
              ('#testing', r'GeeEm, you rolled: kill 20 = [20]'))
        self.geeEm('VellumTalk', '.unalias init', 
              ('GeeEm', r'GeeEm, removed your alias for init'))
        self.geeEm('VellumTalk', '.aliases', 
              ('GeeEm', r'Aliases for GeeEm:   argh=20, foobar=30, kill=20'))

        # testhijack
        self.geeEm('VellumTalk', '*grimlock1 does a [smackdown 1000]', 
              ('GeeEm', 'grimlock1, you rolled: smackdown 1000 = [1000]'))
        self.geeEm('#testing', '*grimlock1 does a [bitchslap 1000]', 
              ('#testing', 'grimlock1, you rolled: bitchslap 1000 = [1000]'))
        self.geeEm('VellumTalk', '*grimlock1 does a [smackdown]', 
              ('GeeEm', 'grimlock1, you rolled: smackdown = [1000]'))
        self.geeEm('VellumTalk', 'I do a [smackdown]')
        self.geeEm('VellumTalk', '.aliases grimlock1', 
              ('GeeEm', 'Aliases for grimlock1:   bitchslap=1000, smackdown=1000'))
        self.geeEm('VellumTalk', '.unalias grimlock1 smackdown', 
              ('GeeEm', 'grimlock1, removed your alias for smackdown'))
        self.geeEm('VellumTalk', '.aliases grimlock1', 
              ('GeeEm', 'Aliases for grimlock1:   bitchslap=1000'))

        # testobserved
        self.geeEm('VellumTalk', '.gm', 
              ('GeeEm', r'GeeEm is now a GM and will observe private messages for session #testing'))
        self.player('VellumTalk', '[stabtastic 20]', 
           ('GeeEm', r'Player, you rolled: stabtastic 20 = [20] (<Player>  [stabtastic 20])'),
           ('Player', r'Player, you rolled: stabtastic 20 = [20] (observed)')
           )

        # testobserverchange
        self.vt.userRenamed('Player', 'Superman')
        self.geeEm("VellumTalk", '[stabtastic 20]',
                ('GeeEm', r'GeeEm, you rolled: stabtastic 20 = [20]')
              )

        # testunobserved
        self.vt.userLeft('GeeEm', '#testing')
        self.player('VellumTalk', '[stabtastic 20]', 
           ('Player', r'Player, you rolled: stabtastic 20 = [20]')
           )

