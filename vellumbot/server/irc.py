"""
Vellum's face.  The bot that answers actions in the channel.
"""
# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, task
from twisted.python import log


from vellumbot.server import linesyntax, d20session, session


MAX_LINE = 420


def splitTextIRCWise(s, width):
    """
    Split s into lines, and for each line longer than width, split it into
    width-long segments.
    """
    lines = s.splitlines()
    ret = []
    for line in lines:
        for n in range((len(line)/width) + 1):
            ret.append(line[n*width:(n+1)*width])
    return ret


class Request(object):
    """
    The state object for privmsgs that are made on the bot
    """
    def __init__(self, user, channel, message):
        self.user = user         # who spoke
        self.channel = channel   # where the reply should go
        self.message = message
        self.sentence = None
        self.recipients = None

    def setRecipients(self, *recipients):
        """
        These people should get the message.
        """
        assert [r for r in recipients if r], "setRecipients called with %r" % (recipients,)
        self.recipients = recipients


class VellumTalk(irc.IRCClient):
    """
    An IRC bot that handles D&D game sessions.
    (Currently contains d20-specific assumption about initiative.)
    """
    
    nickname = "VellumTalk"

    def __init__(self, *args, **kwargs):
        self.wtf = 0  # number of times a "wtf" has occurred recently.
        # reset wtf's every 30 seconds 
        self.resetter = task.LoopingCall(self._resetWtfCount)
        self.resetter.start(30.0)

        self.sessions = []           # list of the sessions the bot is in
        self.defaultSession = None
        # TODO - analyze, do i *really* need responding?
        self.responding = 0          # don't start responding until I join a
                                     # channel
        # no irc.IRCClient.__init__ to call

    def findSessions(self, channel):
        """
        Return the channel that matches channel, or the channel that has
        channel (a nick) in its list of people.

        Otherwise, return the defaultSession, usually indicating that someone
        has /msg'd the bot and that person is not in a channel with the bot.
        """
        found = []
        for session in self.sessions:
            if channel == session.channel:
                found.append(session)
            if session.matchNick(channel):
                found.append(session)
        if found == []:
            found = [self.defaultSession]
        return found

    def _resetWtfCount(self):
        self.wtf = 0

    def respondToUnknown(self):
        # we don't want to get caught looping, so respond up to 3 times
        # with wtf, then wait for the counter to reset
        if self.wtf < 3:
            self.wtf = self.wtf + 1
            self.msg("wtf?")
        if self.wtf < 4:
            log.msg("Spam blocking tripped. WTF counter exceeded.")
            self.wtf = self.wtf + 1
    
    def msgSlowly(self, channel, lines, delay=700):
        """Send multiple lines to the channel with delays in the middle
        delay is given in ms
        """
        send = lambda line: self.msg(channel, line)
        send(lines[0])
        for n, line in enumerate(lines[1:]):
            from . import irc as myself
            if getattr(myself, 'TESTING', False):
                send(line)
            else:
                reactor.callLater(n*(delay/1000.0), send, line)

    def sendResponse(self, response):
        if response is None:
            return
        _already = {}
        for channel, text in response.getMessages():
            # don't send messages to any users twice
            if (channel, text) in _already:
                continue

            # twisted's abstract sockets insist that data be as byte strings.
            if isinstance(text, unicode):
                text = text.encode('utf-8')

            splittext = splitTextIRCWise(text, MAX_LINE)
            log.msg("====> %s:    %s" % (channel, text[:80]))
            if len(splittext) > 1:
                self.msgSlowly(channel, splittext)
            else:
                self.msg(channel, text)
            _already[(channel, text)] = True

    # callbacks for irc events
    # callbacks for irc events
    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        # create a session to respond to private messages from nicks
        # not in any channel I'm in

        self.ircNetwork = u'TODO' # TODO 

        self.defaultSession = self.store.find(d20session.D20Session,
                d20session.D20Session.name == u'#@@default@@').one()
        self.defaultSession.isDefaultSession = True
        # join my default channel
        self.join(self.factory.channel)

    def joined(self, channel):
        """
        When the bot joins a channel, find or make a session and start
        tracking who's in the session.
        """
        # find or make a session
        session = self.findSessions(channel)[0]
        if session is self.defaultSession: # i.e., not found
            session = d20session.D20Session(channel)
            self.sessions.append(session)

        self.responding = 1

    def left(self, channel):
        """
        When the bot parts a channel.
        """
        session = self.findSessions(channel)[0]
        self.sessions.remove(session)

    def kickedFrom(self, channel, kicker, message):
        """
        Don't let the door hit the bot's ass on the way out.
        """
        session = self.findSessions(channel)[0]
        self.sessions.remove(session)

    def userJoined(self, user, channel):
        """
        Some other person joins a channel the bot is already watching.
        """
        session = self.findSessions(channel)[0]
        self.sendResponse(session.addNick(user))

    def userLeft(self, user, channel):
        """
        Some other person leaves a channel the bot is already watching.
        """
        session = self.findSessions(channel)[0]
        self.sendResponse(session.removeNick(user))

    def userQuit(self, user, quitmessage):
        """
        Some other person leaves a channel the bot is already watching (by
        quitting).
        """
        sessions = self.findSessions(user)
        for s in sessions:
            self.sendResponse(s.removeNick(user))

    def userKicked(self, user, channel, kicker, kickmessage):
        session = self.findSessions(channel)[0]
        self.sendResponse(session.removeNick(user))

    def userRenamed(self, old, new):
        """
        Some other person does a /nick change in a channel the bot is
        watching.
        """
        sessions = self.findSessions(old)
        for s in sessions:
            self.sendResponse(s.rename(old, new))

    def irc_RPL_NAMREPLY(self, prefix, (user, _, channel, names)):
        """
        After joining a channel, the irc server tells us who's there, this
        gets called to keep track.
        """
        nicks = names.split()
        for nick in nicks[:]:
            if nick[0] in '@+':
                nicks.remove(nick)
                nicks.append(nick[1:])

        session = self.findSessions(channel)[0]
        self.sendResponse(session.addNick(*nicks))

    def irc_RPL_ENDOFNAMES(self, prefix, params):
        pass

    def irc_unknown(self, prefix, command, params):
        log.msg('|||'.join((prefix, command, repr(params))))

    def irc_INVITE(self, prefix, (user, channel)):
        """
        Some nice person invited the bot to join a channel.  Do so.
        """
        self.join(channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        log.msg(user, channel, msg)
        if not self.responding:
            return
        # Check to see if they're sending me a private message
        # If so, the return channel is the user.
        observers = []
        if channel.lower() == self.nickname.lower():
            respondTo = user
            ses = self.defaultSession
            for s in self.findSessions(user):
                observers.extend(s.observers)
        else:
            respondTo = channel
            ses = self.findSessions(channel)[0]

        try:
            sentence = linesyntax.parseSentence(msg)
        except RuntimeError:
            return

        req = Request(user, respondTo, msg)
        req.sentence = sentence

        if sentence.command:
            # ignore people talking to other people
            if sentence.botName is not None and sentence.botName != self.nickname.lower():
                return

            if respondTo == user:
                response = ses.privateCommand(req, *observers)
            else:
                response = ses.command(req)
            self.sendResponse(response)
        elif sentence.verbPhrases:
            if respondTo == user:
                response = ses.privateInteraction(req, *observers)
            else:
                response = ses.interaction(req)
            self.sendResponse(response)
        else:
            pass

    # though it looks weird, actions will behave the same way as privmsgs.
    # for example, /me .hello will behave like "VellumTalk: hello" or ".hello"
    action = privmsg


class VellumTalkFactory(protocol.ClientFactory):
    """A factory for VellumTalks.

    A new protocol instance will be created each time we connect to the server.

    VellumTalkFactory(channel) => a bot factory which will join the given
    channel after connecting.
    """

    # the class of the protocol to build when new connection is made
    protocol = VellumTalk 

    def __init__(self, channel):
        self.channel = channel
        # no protocol.ClientFactory.__init__ to call

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()

