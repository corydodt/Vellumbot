import operator

from twisted.test.proto_helpers import StringTransport

from vellumbot.server import irc
from vellumbot.user import User, userDatabase
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

        geeEm = lambda *a, **kw: self.anyone('GeeEm', *a, **kw)
        ugm = self.addUser(u"GeeEm")
        uplayer = self.addUser(u"Player")

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

    def test_aliasesForMissing(self):
        """
        The bot does not barf when we try to access the aliases of an unknown
        person.
        """
        geeEm = lambda *a, **kw: self.anyone('GeeEm', *a, **kw)
        ugm = self.addUser(u"GeeEm")

        geeEm('VellumTalk', ".aliases unknownPersonX", 
                ('GeeEm', 'No such user known: unknownPersonX'))

        geeEm('VellumTalk', ".unalias unknownPersonX spot", 
                ('GeeEm', 'No such user known: unknownPersonX'))

    def test_closingQuotation(self):
        """
        quotes seem to cause issues in this odd corner case
        """
        vellumbot.server.session.TESTING = True
        vellumbot.server.irc.TESTING = True

        geeEm = lambda *a, **kw: self.anyone('GeeEm', *a, **kw)
        ugm = self.addUser(u"GeeEm")
        # this seems to be the minimum necessary to reproduce the bug
        geeEm('#testing', "n: o p. q'r")

    def test_gibberishCommands(self):
        """
        Speaking gibberish commands to the bot does not flail
        """
        geeEm = lambda *a, **kw: self.anyone('GeeEm', *a, **kw)
        ugm = self.addUser(u"GeeEm")

        geeEm('VellumTalk', '.adf91', ('GeeEm', 'wtf!?'))

        # empty commands are ignored
        geeEm('VellumTalk', '.', )

    def test_impersonate(self):
        """
        We can use the * syntax to impersonate another
        """
        geeEm = lambda *a, **kw: self.anyone('GeeEm', *a, **kw)

        ugm = self.addUser(u"GeeEm")

        geeEm('VellumTalk', '*grimlock1 does a [smack down1 1000]', 
              ('GeeEm', 'grimlock1, you rolled: smack down1 1000 = \[1000\]'))
        geeEm('#testing', '*grimlock1 does a [bitchslap 1000]', 
              ('#testing', 'grimlock1, you rolled: bitchslap 1000 = \[1000\]'))
        geeEm('VellumTalk', '*grimlock1 does a [smack down1]', 
              ('GeeEm', 'grimlock1, you rolled: smack down1 = \[1000\]'))
        geeEm('VellumTalk', 'I do a [smack down1]')
        geeEm('VellumTalk', '.aliases grimlock1', 
              ('GeeEm', 'Aliases for grimlock1:   bitchslap=1000, smack down1=1000'))
        geeEm('VellumTalk', '.unalias grimlock1 "smack down1"', 
              ('GeeEm', 'grimlock1, removed your alias for smack down1'))
        geeEm('VellumTalk', '.aliases grimlock1', 
              ('GeeEm', 'Aliases for grimlock1:   bitchslap=1000'))

    def test_connectionMade(self):
        # set up a protocol instance similar to what we do in BotTestCase.setUp
        transport = StringTransport()
        vt = irc.VellumTalk()
        fac = util.FakeFactory()
        fac.store = userDatabase('sqlite:')
        fac.serverEncoding = 'utf-8'
        vt.factory = fac

        vt.makeConnection(transport)
        self.assertIdentical(vt.store, fac.store)
        vt.resetter.stop()

    def test_botSignon(self):
        """
        When the bot signs on, it joins the right channels and such
        """
        # clean out the defaultSession, so as to test its creation
        self.vt.defaultSession = None
        self.vt.factory = irc.VellumTalkFactory('#vellum')
        self.vt.signedOn()
        self.assertTrue(self.vt.defaultSession.isDefaultSession)

    def test_botJoinLeave(self):
        """
        When the bot joins a channel, users in there are hooked up correctly.
        When it leaves, they are unhooked.
        """
        self.vt.responding = 0
        self.vt.joined("#xyz")
        _xyz = self.vt.findSessions(u'#xyz')[0]
        self.assertEqual(_xyz.name, u'#xyz')
        self.assertEqual(self.vt.responding, 1)

        # When IRC sends us some names, check that the box is aware of them.
        self.vt.irc_RPL_NAMREPLY('_ignored1_', ('_ignored2_', '_ignored3_', '#xyz', 
            'Player1 Player2 Player3'))
        subs = sorted(map(operator.attrgetter('name'), _xyz.subSessions))
        self.assertEqual(subs, [u'Player1', u'Player2', u'Player3'])

        # bot leaves
        self.vt.left('#xyz')
        self.assertEqual(self.vt.findSessions(u'#xyz'),
                [self.vt.defaultSession])

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
        self.assertEqual(len(t1.subSessions), 1)

        self.vt.userJoined("Player", "#testing2")
        self.assertEqual(len(t1.subSessions), 1)
        self.assertEqual(len(t2.subSessions), 1)

        self.vt.userKicked("Player", "#testing1", "GM", "f u")
        self.assertEqual(len(t1.subSessions), 0)
        self.assertEqual(len(t2.subSessions), 1)

        self.vt.userJoined("Player", "#testing3")
        self.assertEqual(len(t3.subSessions), 1)

        self.vt.userLeft("Player", "#testing3")
        self.assertEqual(len(t3.subSessions), 0)
        self.assertEqual(len(t2.subSessions), 1)
        self.assertEqual(len(t1.subSessions), 0)

        self.vt.userJoined("Player", "#testing3")
        self.assertEqual(len(t3.subSessions), 1)
        self.assertEqual(len(t2.subSessions), 1)

        self.vt.userQuit("Player", "f u too")
        self.assertEqual(len(t3.subSessions), 0)
        self.assertEqual(len(t2.subSessions), 0)
        self.assertEqual(len(t1.subSessions), 0)

    def test_renames(self):
        """
        When a user changes nicks, I change their nicks in all affected
        sessions.
        """
        self.vt.userJoined("Player", "#testing1")
        self.vt.userJoined("Player", "#testing2")

        # make sure there is exactly one user named Player right now in the
        # database
        self.assertTrue(self.vt.store.find(User, 
            User.name==u'Player').one() is not None)
        # ... and none named Player1
        self.assertTrue(self.vt.store.find(User, 
            User.name==u'Player1').one() is None)

        t1 = self.vt.findSessions("#testing1")[0]
        t2 = self.vt.findSessions("#testing2")[0]
        self.assertEqual(list(t1.subSessions)[0].name, u"Player")
        self.assertEqual(list(t2.subSessions)[0].name, u"Player")
        self.assertEqual(len(t1.subSessions), 1)
        self.assertEqual(len(t2.subSessions), 1)

        self.vt.userRenamed("Player", "Player1")
        self.assertEqual(len(list(t1.subSessions)), 1, "More (or less) than 1 Player in #testing1 after rename")
        self.assertEqual(len(list(t2.subSessions)), 1, "More (or less) than 1 Player in #testing2 after rename")
        self.assertEqual(list(t1.subSessions)[0].name, u"Player1")
        self.assertEqual(list(t2.subSessions)[0].name, u"Player1")

        # same set of assertions about the database as before, in reverse
        self.assertTrue(self.vt.store.find(User, 
            User.name==u'Player').one() is None)
        self.assertTrue(self.vt.store.find(User, 
            User.name==u'Player1').one() is not None)

    def test_observers(self):
        """
        Check that the gm gets the correct observer messages (including no
        messages, sometimes) when observing a channel.
        """
        player = lambda *a, **kw: self.anyone('Player', *a, **kw)
        superman = lambda *a, **kw: self.anyone('Superman', *a, **kw)
        player2 = lambda *a, **kw: self.anyone('Player2', *a, **kw)
        geeEm = lambda *a, **kw: self.anyone('GeeEm', *a, **kw)

        uplayer = self.addUser(u'Player')
        uplayer2 = self.addUser(u'Player2')
        ugeeEm = self.addUser(u'GeeEm')

        geeEm('#testing', '.gm', 
              ('#testing', r'GeeEm is now a GM and will observe private messages for session #testing'))

        # players who are not in the same channel as the gm should not be
        # observed by the gm:
        player('VellumTalk', '[stabtastic 20]', 
           ('Player', r'Player, you rolled: stabtastic 20 = \[20\]'),
           )

        self.vt.userJoined("Player", "#testing")
        self.assertEqual(list(self.vt.findSessions("#testing")[0].subSessions)[0],
                uplayer)
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
        superman('VellumTalk', '[stabtastic 23]', 
           ('Superman', r'Superman, you rolled: stabtastic 23 = \[23\]')
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
        tryTheseNicks(u"GeeEm", u"Player")
        tryTheseNicks(u"MFen", u"MoonFallen")
        tryTheseNicks(u"bbb", u"aa")

    def test_nickCaseFolding(self):
        """
        IRC servers that send me the nick lowercased will still match
        """
        player = lambda *a, **kw: self.anyone('Player', *a, **kw)
        self.addUser(u'Player')

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
        self.addUser(nick.decode('utf-8'))

        veryLongNick("VellumTalk", ".hello", *lines)
