from twisted.trial import unittest
import re

from twisted.internet import protocol
from twisted.words.test.test_irc import StringIOWithoutClosing

from vellumbot.server import alias, d20session
from vellumbot.server.irc import VellumTalk
import vellumbot.server.session
from . import util



class ByteStringIOWithoutClosing(StringIOWithoutClosing):
    def write(self, data):
        # mimic real twisted's insistence on unicode
        if isinstance(data, unicode): # no, really, I mean it
            raise TypeError("Data must not be unicode")
        return StringIOWithoutClosing.write(self, data)


def formPrivMsg(*recipients):
    if recipients:
        r = ["PRIVMSG %s :%s" % (targ,exp) for targ,exp in recipients]
        return "\n".join(r)
    return ''


NL = re.compile(r'\r?\n')

class ResponseTest:
    """Notation for testing a response to a command."""
    def __init__(self, factory, user, channel, sent, expectation):
        self.user = user
        self.factory = factory
        self.channel = channel
        self.sent = sent

        if isinstance(expectation, list):
            expectation = '\n'.join(expectation)

        self.expectation = expectation

        self.last_pos = 0

    def getActual(self):
        """
        Pull the actual data from the pipe, and set the pipe state for next
        time
        """
        pipe = self.factory.pipe
        pipe.seek(self.factory.pipe_pos)
        actual = pipe.read().strip()
        self.factory.pipe_pos = pipe.tell()
        return actual

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


class ResponseTestFactory:
    def __init__(self, pipe):
        self.pipe = pipe
        self.pipe_pos = 0

    def next(self, user, channel, target, *recipients):
        expectation = formPrivMsg(*recipients)
        return ResponseTest(self,
                            user,
                            channel, 
                            target, 
                            expectation)


class IRCTestCase(unittest.TestCase, util.DiffTestCaseMixin):
    factory = None

    def setUp(self):
        if self.factory is None:
            pipe = ByteStringIOWithoutClosing()
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

    def tearDown(self):
        self.vt.resetter.stop()

    def geeEm(self, channel, target, *recipients):
        r = self.factory.next('GeeEm', channel, target, *recipients)
        self.vt.privmsg(r.user, r.channel, r.sent)
        r.check(self)

    def player(self, channel, target, *recipients):
        r = self.factory.next('Player', channel, target, *recipients)
        self.vt.privmsg(r.user, r.channel, r.sent)
        r.check(self)

    def test_reference(self):
        vellumbot.server.session.TESTING = True
        vellumbot.server.irc.TESTING = True
        self.geeEm('VellumTalk', '.gm', 
              ('GeeEm', r'GeeEm is now a GM and will observe private messages for session #testing'))

        lines1 = '''"cure light wounds mass": **Cure** Light Wounds, Mass Conjuration ...  positive energy to **cure** 1d8 points of damag ... reature. Like other **cure** spells, mass **cure** l ... 
"cure minor wounds": **Cure** Minor Wounds Conjuration (Heal ... pell functions like **cure** light wounds , exce ... pt that it **cure**s only 1 point of da ... 
"cure critical wounds": **Cure** Critical Wounds Conjuration (H ... pell functions like **cure** light wounds , exce ... pt that it **cure**s 4d8 points of dama ... 
"cure critical wounds mass": **Cure** Critical Wounds, Mass Conjurat ... functions like mass **cure** light wounds , exce ... pt that it **cure**s 4d8 points of dama ... 
"cure moderate wounds mass": **Cure** Moderate Wounds, Mass Conjurat ... functions like mass **cure** light wounds , exce ... pt that it **cure**s 2d8 points of dama ... '''.split('\n')

        expectations1 = []
        for line in lines1:
            expectations1.append(('Player', '%s \(observed\)' % (re.escape(line),)))
            expectations1.append(('GeeEm', '%s \(<Player>  \.lookup spell cure\)' % (re.escape(line),)))
        expectations1.append(('Player', 
            r'Replied to Player with top 5 matches for SPELL "cure" \(observed\)'))
        expectations1.append(('GeeEm', 
            r'Replied to Player with top 5 matches for SPELL "cure" \(<Player>  \.lookup spell cure\)'))

        self.player('VellumTalk', '.lookup spell cure', *expectations1)

        expectations2 = []
        for line in lines1:
            expectations2.append(('Player', '%s' % (re.escape(line),)))
        expectations2.append(('#testing', 
            r'Replied to Player with top 5 matches for SPELL "cure"'))

        self.player('#testing', '.lookup spell cure', *expectations2)

        self.player('#testing', '.lookup spell cure serious wounds mass', (
'#testing', r'Player: SPELL <<Cure .*, Mass>> Conjuration \(Healing\) || Level: Cleric 7, Druid 8 || This spell functions like .* +35\)\.'),
                )

        self.player('#testing', '.lookup spell wenis', (
'#testing', r'Player: No SPELL contains "wenis"\.  Try searching with a wildcard e\.g\. \.lookup spell wenis\*'),
                )
        self.player('#testing', '.lookup spell wenis*', (
'#testing', r'Player: No SPELL contains "wenis\*"\.'),
                )

        lines2 = '''"heal": Heal Conjuration \(Healing\) Level: C \.\.\.
"heal mass": Heal, Mass Conjuration \(Healing\) Le \.\.\.
"heal mount": Heal Mount Conjuration \(Healing\) Le \.\.\.
"seed heal": Seed: Heal Conjuration \(Healing\) Sp \.\.\.
"cure critical wounds": Cure Critical Wounds Conjuration \(H \.\.\.'''.split('\n')
        expectations3 = []
        for line in lines2:
            expectations3.append(('Player', line))
        expectations3.append(('#testing', 'Replied to Player with top 5 matches for SPELL "heal\*"'))
        self.player('#testing', '.lookup spell heal*', *expectations3)


    def test_everything(self):
        vellumbot.server.session.TESTING = True
        vellumbot.server.irc.TESTING = True
        self.geeEm('VellumTalk', 'hello')
        self.geeEm('VellumTalk', 'OtherGuy: hello')
        self.geeEm('VellumTalk', 'VellumTalk: hello', ('GeeEm', r'Hello GeeEm\.'))
        self.geeEm('VellumTalk', 'Vellumtalk: hello there', 
            ('GeeEm', r'Hello GeeEm\.'))
        self.geeEm('VellumTalk', '.hello', ('GeeEm', r'Hello GeeEm\.'))
        self.geeEm('#testing', 'hello',)
        self.geeEm('#testing', 'VellumTalk: hello', ('#testing', r'Hello GeeEm\.'))
        self.geeEm('#testing', '.hello', ('#testing', r'Hello GeeEm\.'))
        self.geeEm('VellumTalk', '.inits', ('GeeEm', r'Initiative list: \(none\)'))
        self.geeEm('VellumTalk', '.combat', 
            ('GeeEm', r'\*\* Beginning combat \*\*'))
        self.geeEm('#testing', '[4d1+2]', 
              ('#testing', r'GeeEm, you rolled: 4d1\+2 = \[1\+1\+1\+1\+2 = 6\]'))
        self.geeEm('#testing', '[init 20]', 
              ('#testing', r'GeeEm, you rolled: init 20 = \[20\]'))
        self.geeEm('VellumTalk', '.n', ('GeeEm', r'\+\+ New round \+\+'))
        self.geeEm('VellumTalk', '.n', 
              ('GeeEm', r'GeeEm \(init 20\) is ready to act \. \. \.'))
        self.geeEm('VellumTalk', '.p', ('GeeEm', r'\+\+ New round \+\+'))
        self.geeEm('VellumTalk', '.p', 
              ('GeeEm', r'GeeEm \(init 20\) is ready to act \. \. \.'))
        self.geeEm('VellumTalk', '.inits', 
              ('GeeEm', r'Initiative list: GeeEm/20, NEW ROUND/9999'))
        # self.geeEm('VellumTalk', '.help', ('GeeEm', r's+hello: Greet.')), FIXME
        self.geeEm('VellumTalk', '.aliases', ('GeeEm', r'Aliases for GeeEm:   init=20'))
        self.geeEm('VellumTalk', '.aliases GeeEm', 
              ('GeeEm', r'Aliases for GeeEm:   init=20'))
        self.geeEm('VellumTalk', '.aliases GeeEm Player',   
               ('GeeEm', 'Aliases for GeeEm:   init=20'), 
               ('GeeEm', 'Aliases for Player:   \(none\)'))
        self.geeEm('VellumTalk', '.unalias foobar', 
              ('GeeEm', r'\*\* No alias "foobar" for GeeEm'))
        self.geeEm('#testing',  'hello [argh 20] [foobar 30]', 
              ('#testing', r'GeeEm, you rolled: argh 20 = \[20\]'),
              ('#testing', r'GeeEm, you rolled: foobar 30 = \[30\]'))
        self.geeEm('#testing',  '[argh +1]', 
              ('#testing', r'GeeEm, you rolled: argh \+1 = \[20\+1 = 21\]'))
        self.geeEm('#testing',  'I will [kill 20] them @all', 
              ('#testing', r'GeeEm, you rolled: kill 20 = \[20\]'))
        self.geeEm('VellumTalk', '.unalias init', 
              ('GeeEm', r'GeeEm, removed your alias for init'))
        self.geeEm('VellumTalk', '.aliases', 
              ('GeeEm', r'Aliases for GeeEm:   argh=20, foobar=30, kill=20'))

        # testhijack
        self.geeEm('VellumTalk', '*grimlock1 does a [smackdown 1000]', 
              ('GeeEm', 'grimlock1, you rolled: smackdown 1000 = \[1000\]'))
        self.geeEm('#testing', '*grimlock1 does a [bitchslap 1000]', 
              ('#testing', 'grimlock1, you rolled: bitchslap 1000 = \[1000\]'))
        self.geeEm('VellumTalk', '*grimlock1 does a [smackdown]', 
              ('GeeEm', 'grimlock1, you rolled: smackdown = \[1000\]'))
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
           ('Player', r'Player, you rolled: stabtastic 20 = \[20\] \(observed\)'),
           ('GeeEm', r'Player, you rolled: stabtastic 20 = \[20\] \(<Player>  \[stabtastic 20\]\)'),
           )

        # testobserverchange
        self.vt.userRenamed('Player', 'Superman')
        self.geeEm("VellumTalk", '[stabtastic 20]',
                ('GeeEm', r'GeeEm, you rolled: stabtastic 20 = \[20\]')
              )

        # testunobserved
        self.vt.userLeft('GeeEm', '#testing')
        self.player('VellumTalk', '[stabtastic 20]', 
           ('Player', r'Player, you rolled: stabtastic 20 = \[20\]')
           )

