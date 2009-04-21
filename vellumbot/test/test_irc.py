from vellumbot.server import d20session, irc
import vellumbot.server.session
from . import util


class IRCTestCase(util.BotTestCase):
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
        geeEm('#testing', '[init 20]', 
              ('#testing', r'GeeEm, you rolled: init 20 = \[20\]'))
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

    def test_impersonate(self):
        """
        We can use the * syntax to impersonate another
        """
        geeEm = lambda *a, **kw: self.anyone('GeeEm', *a, **kw)
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

    def test_nickOrderSensitive(self):
        """
        Observer/observee order is respected (fixed a bug)
        """
        def tryTheseNicks(gmName, playerName):
            self.vt.userJoined(playerName, "#testing")
            self.vt.userJoined(gmName, "#testing")
            player = lambda *a, **kw: self.anyone(playerName, *a, **kw)
            geeEm = lambda *a, **kw: self.anyone(gmName, *a, **kw)

            geeEm("#testing", ".gm", 
              ('#testing', r'%s is now a GM and will observe private messages for session #testing' % (
                       gmName,)
                   )
            )
            player('VellumTalk', '[stabtastic 24]', 
               (playerName, r'%s, you rolled: stabtastic 24 = \[24\] \(observed\)' % (
                   playerName,)
                   ),
               (gmName, r'<%s>  \[stabtastic 24\]  ===>  %s, you rolled: stabtastic 24' % (
                   playerName, playerName)
                   ),
            )
            self.vt.userLeft(playerName, "#testing")
            self.vt.userLeft(gmName, "#testing")
        # try a few different nicks so we get a different arbitrary sort order
        tryTheseNicks("GeeEm", "Player")
        tryTheseNicks("MFen", "MoonFallen")
        tryTheseNicks("aa", "bbb")

    def test_nickCaseFolding(self):
        """
        IRC servers that send me the nick lowercased will still match
        """
        player = lambda *a, **kw: self.anyone('Player', *a, **kw)
        player("VellumTalk", ".hello",
                ("Player", "Hello Player."))
        player("vellumtalk", ".hello",
                ("Player", "Hello Player."))

    def test_veryLongMessage(self):
        """
        Very long messages get split sensibly across lines
        """
        nick = ''.join(["%dBilly"%(n%10) for n in range(80)])
        message = "Hello %s" % (nick,) + "."

        lines = []
        for n in range((len(nick)/irc.MAX_LINE) + 1):
            lines.append((nick, message[n*irc.MAX_LINE:(n+1)*irc.MAX_LINE]+r'$'))

        veryLongNick = lambda *a, **kw: self.anyone(nick, *a, **kw)

        veryLongNick("VellumTalk", ".hello", *lines)
