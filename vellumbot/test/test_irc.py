from twisted.trial import unittest
import re

from twisted.internet import protocol
from twisted.test.proto_helpers import StringTransport

from vellumbot.server import alias, d20session
from vellumbot.server.irc import VellumTalk
import vellumbot.server.session
from . import util



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


class IRCTestCase(unittest.TestCase, util.DiffTestCaseMixin):

    def setUp(self):
        # TODO - move d20-specific tests, e.g. init and other alias hooks?
        # save off and clear alias.aliases, since it gets persisted # FIXME
        orig_aliases = alias.aliases
        alias.aliases = {}

        self.transport = StringTransport()
        vt = self.vt = VellumTalk()
        vt.performLogin = 0
        vt.joined("#testing")
        vt.defaultSession = d20session.D20Session('')
        vt.makeConnection(self.transport)

    def tearDown(self):
        self.vt.resetter.stop()

    def anyone(self, who, channel, target, *recipients):
        """
        Simulate an interaction between the named person and VellumTalk
        """
        r = ResponseTest(self.transport, who, channel, target, *recipients)
        self.vt.privmsg(r.user, r.channel, r.sent)
        r.check(self)

    def test_reference(self):
        """
        I respond to people who look things up
        """
        vellumbot.server.session.TESTING = True
        vellumbot.server.irc.TESTING = True
        geeEm = lambda *a, **kw: self.anyone('GeeEm', *a, **kw)
        player = lambda *a, **kw: self.anyone('Player', *a, **kw)

        self.vt.userJoined("Player", "#testing")

        geeEm('#testing', '.gm', 
              ('#testing', r'GeeEm is now a GM and will observe private messages for session #testing'))

        lines1 = '''"cure light wounds mass": **Cure** Light Wounds, Mass Conjuration ...  positive energy to **cure** 1d8 points of damag ... reature. Like other **cure** spells, mass **cure** l ... 
"cure minor wounds": **Cure** Minor Wounds Conjuration (Heal ... pell functions like **cure** light wounds , exce ... pt that it **cure**s only 1 point of da ... 
"cure critical wounds": **Cure** Critical Wounds Conjuration (H ... pell functions like **cure** light wounds , exce ... pt that it **cure**s 4d8 points of dama ... 
"cure critical wounds mass": **Cure** Critical Wounds, Mass Conjurat ... functions like mass **cure** light wounds , exce ... pt that it **cure**s 4d8 points of dama ... 
"cure moderate wounds mass": **Cure** Moderate Wounds, Mass Conjurat ... functions like mass **cure** light wounds , exce ... pt that it **cure**s 2d8 points of dama ... '''.split('\n')

        expectations1 = []
        for line in lines1:
            expectations1.append(('Player', '%s \(observed\)' % (re.escape(line),)))
            expectations1.append(('GeeEm', '<Player>  \.lookup spell cure  ===>  %s' % (re.escape(line),)))
        expectations1.append(('Player', 
            r'Replied to Player with top 5 matches for SPELL "cure" \(observed\)'))
        expectations1.append(('GeeEm', 
            r'<Player>  \.lookup spell cure  ===>  Replied to Player with top 5 matches for SPELL "cure"'))

        player('VellumTalk', '.lookup spell cure', *expectations1)

        expectations2 = []
        for line in lines1:
            expectations2.append(('Player', '%s' % (re.escape(line),)))
        expectations2.append(('#testing', 
            r'Replied to Player with top 5 matches for SPELL "cure"'))

        player('#testing', '.lookup spell cure', *expectations2)

        player('#testing', '.lookup spell cure serious wounds mass', (
'#testing', r'Player: SPELL <<Cure .*, Mass>> Conjuration \(Healing\) || Level: Cleric 7, Druid 8 || This spell functions like .* +35\)\.'),
                )

        player('#testing', '.lookup spell wenis', (
'#testing', r'Player: No SPELL contains "wenis"\.  Try searching with a wildcard e\.g\. \.lookup spell wenis\*'),
                )
        player('#testing', '.lookup spell wenis*', (
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
        player('#testing', '.lookup spell heal*', *expectations3)

        player('#testing', '.lookup monster mohrg', (
'#testing', r'Player: MONSTER <<Mohrg>> Chaotic Evil .*mohrg.htm')
                )

    def test_failedReference(self):
        """
        Lookups that refer to things that I don't know how to look up give an
        error.
        """
        vellumbot.server.session.TESTING = True
        vellumbot.server.irc.TESTING = True
        self.anyone('Player', '#testing', '.lookup feat cleave', 
                ('#testing', 'I don\'t know how to look those things up.'))

    def test_commandsAndSentences(self):
        """
        Commands, either spoken as ".command" or "vellumtalk: command" and
        sentences with dice expressions are recognized.

        Things that are not sentences or commands are ignored.
        """
        vellumbot.server.session.TESTING = True
        vellumbot.server.irc.TESTING = True
        self.vt.defaultSession = d20session.D20Session('#testing')
        geeEm = lambda *a, **kw: self.anyone('GeeEm', *a, **kw)
        geeEm('VellumTalk', 'hello')
        geeEm('VellumTalk', 'OtherGuy: hello')
        geeEm('VellumTalk', 'VellumTalk: hello', ('GeeEm', r'Hello GeeEm\.'))
        geeEm('VellumTalk', 'Vellumtalk: hello there', 
            ('GeeEm', r'Hello GeeEm\.'))
        geeEm('VellumTalk', '.hello', ('GeeEm', r'Hello GeeEm\.'))
        geeEm('#testing', 'hello',)
        geeEm('#testing', 'VellumTalk: hello', ('#testing', r'Hello GeeEm\.'))
        geeEm('#testing', '.hello', ('#testing', r'Hello GeeEm\.'))
        geeEm('VellumTalk', '.inits', ('GeeEm', r'Initiative list: \(none\)'))
        geeEm('VellumTalk', '.combat', 
            ('GeeEm', r'\*\* Beginning combat \*\*'))
        geeEm('#testing', '[4d1+2]', 
              ('#testing', r'GeeEm, you rolled: 4d1\+2 = \[1\+1\+1\+1\+2 = 6\]'))
        geeEm('#testing', '[init 20]', 
              ('#testing', r'GeeEm, you rolled: init 20 = \[20\]'))
        geeEm('VellumTalk', '.n', ('GeeEm', r'\+\+ New round \+\+'))
        geeEm('VellumTalk', '.n', 
              ('GeeEm', r'GeeEm \(init 20\) is ready to act \. \. \.'))
        geeEm('VellumTalk', '.p', ('GeeEm', r'\+\+ New round \+\+'))
        geeEm('VellumTalk', '.p', 
              ('GeeEm', r'GeeEm \(init 20\) is ready to act \. \. \.'))
        geeEm('VellumTalk', '.inits', 
              ('GeeEm', r'Initiative list: GeeEm/20, NEW ROUND/9999'))
        # geeEm('VellumTalk', '.help', ('GeeEm', r's+hello: Greet.')), FIXME
        geeEm('VellumTalk', '.aliases', ('GeeEm', r'Aliases for GeeEm:   init=20'))
        geeEm('VellumTalk', '.aliases GeeEm', 
              ('GeeEm', r'Aliases for GeeEm:   init=20'))
        geeEm('VellumTalk', '.aliases GeeEm Player',   
               ('GeeEm', 'Aliases for GeeEm:   init=20'), 
               ('GeeEm', 'Aliases for Player:   \(none\)'))
        geeEm('VellumTalk', '.unalias foobar', 
              ('GeeEm', r'\*\* No alias "foobar" for GeeEm'))
        geeEm('#testing',  'hello [argh 20] [foobar 30]', 
              ('#testing', r'GeeEm, you rolled: argh 20 = \[20\]'),
              ('#testing', r'GeeEm, you rolled: foobar 30 = \[30\]'))
        geeEm('#testing',  '[argh +1]', 
              ('#testing', r'GeeEm, you rolled: argh \+1 = \[20\+1 = 21\]'))
        geeEm('#testing',  'I will [kill 20] them @all', 
              ('#testing', r'GeeEm, you rolled: kill 20 = \[20\]'))
        geeEm('VellumTalk', '.unalias init', 
              ('GeeEm', r'GeeEm, removed your alias for init'))
        geeEm('VellumTalk', '.aliases', 
              ('GeeEm', r'Aliases for GeeEm:   argh=20, foobar=30, kill=20'))

        # testhijack
        geeEm('VellumTalk', '*grimlock1 does a [smackdown 1000]', 
              ('GeeEm', 'grimlock1, you rolled: smackdown 1000 = \[1000\]'))
        geeEm('#testing', '*grimlock1 does a [bitchslap 1000]', 
              ('#testing', 'grimlock1, you rolled: bitchslap 1000 = \[1000\]'))
        geeEm('VellumTalk', '*grimlock1 does a [smackdown]', 
              ('GeeEm', 'grimlock1, you rolled: smackdown = \[1000\]'))
        geeEm('VellumTalk', 'I do a [smackdown]')
        geeEm('VellumTalk', '.aliases grimlock1', 
              ('GeeEm', 'Aliases for grimlock1:   bitchslap=1000, smackdown=1000'))
        geeEm('VellumTalk', '.unalias grimlock1 smackdown', 
              ('GeeEm', 'grimlock1, removed your alias for smackdown'))
        geeEm('VellumTalk', '.aliases grimlock1', 
              ('GeeEm', 'Aliases for grimlock1:   bitchslap=1000'))

    def test_joinKickLeaveQuit(self):
        """
        When a user joins, I add them to a session.  When kicked, I remove them.
        """
        self.vt.joined("#testing1")
        self.vt.joined("#testing2")
        self.vt.joined("#testing3")
        t1 = self.vt.findSessions("#testing1")[0]
        t2 = self.vt.findSessions("#testing2")[0]
        t3 = self.vt.findSessions("#testing3")[0]

        self.vt.userJoined("Player", "#testing1")
        self.assertEqual(len(t1.nicks), 1)

        self.vt.userJoined("Player", "#testing2")
        self.assertEqual(len(t1.nicks), 1)
        self.assertEqual(len(t2.nicks), 1)

        self.vt.userKicked("Player", "#testing1", "GM", "f u")
        self.assertEqual(len(t1.nicks), 0)
        self.assertEqual(len(t2.nicks), 1)

        self.vt.userJoined("Player", "#testing3")
        self.assertEqual(len(t3.nicks), 1)

        self.vt.userLeft("Player", "#testing3")
        self.assertEqual(len(t3.nicks), 0)
        self.assertEqual(len(t2.nicks), 1)
        self.assertEqual(len(t1.nicks), 0)

        self.vt.userJoined("Player", "#testing3")
        self.assertEqual(len(t3.nicks), 1)
        self.assertEqual(len(t2.nicks), 1)

        self.vt.userQuit("Player", "f u too")
        self.assertEqual(len(t3.nicks), 0)
        self.assertEqual(len(t2.nicks), 0)
        self.assertEqual(len(t1.nicks), 0)

    def test_renames(self):
        """
        When a user changes nicks, I change their nicks in all affected
        sessions.
        """
        self.vt.userJoined("Player", "#testing1")
        self.vt.userJoined("Player", "#testing2")
        t1 = self.vt.findSessions("#testing1")[0]
        t2 = self.vt.findSessions("#testing2")[0]
        self.assertEqual(list(t1.nicks)[0], "Player")
        self.assertEqual(list(t2.nicks)[0], "Player")
        self.assertEqual(len(t1.nicks), 1)
        self.assertEqual(len(t2.nicks), 1)

        self.vt.userRenamed("Player", "Player1")
        self.assertEqual(list(t1.nicks)[0], "Player1")
        self.assertEqual(list(t2.nicks)[0], "Player1")

    def test_observers(self):
        """
        Check that the gm gets the correct observer messages (including no
        messages, sometimes) when observing a channel.
        """
        player = lambda *a, **kw: self.anyone('Player', *a, **kw)
        player2 = lambda *a, **kw: self.anyone('Player2', *a, **kw)
        geeEm = lambda *a, **kw: self.anyone('GeeEm', *a, **kw)
        geeEm('#testing', '.gm', 
              ('#testing', r'GeeEm is now a GM and will observe private messages for session #testing'))

        # players who are not in the same channel as the gm should not be
        # observed by the gm:
        player('VellumTalk', '[stabtastic 20]', 
           ('Player', r'Player, you rolled: stabtastic 20 = \[20\]'),
           )

        self.vt.userJoined("Player", "#testing")
        self.assertEqual(list(self.vt.findSessions("#testing")[0].nicks)[0], "Player")
        s0 = self.vt.findSessions("testing")[0]

        # players who ARE in the same channel as the gm get observed:
        player('VellumTalk', '[stabtastic 21]', 
           ('Player', r'Player, you rolled: stabtastic 21 = \[21\] \(observed\)'),
           ('GeeEm', r'<Player>  \[stabtastic 21\]  ===>  Player, you rolled: stabtastic 21'),
           )

        # testobserverchange
        self.vt.userRenamed('Player', 'Superman')
        geeEm("VellumTalk", '[stabtastic 22]',
                ('GeeEm', r'GeeEm, you rolled: stabtastic 22 = \[22\]')
              )

        # testunobserved
        self.vt.userLeft('GeeEm', '#testing')
        player('VellumTalk', '[stabtastic 23]', 
           ('Player', r'Player, you rolled: stabtastic 23 = \[23\]')
           )

