"""
Vellum's face.  The bot that answers actions in the channel.
"""
# system imports
import sys
import re

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, task
from twisted.python import log


from vellumbot.server import linesyntax, d20session, alias


class VellumTalk(irc.IRCClient):
    """
    An IRC bot that handles D&D game sessions.
    (Currently contains d20-specific assumption about initiative.)
    """
    
    nickname = "VellumTalk"

    def __init__(self, *args, **kwargs):
        self.wtf = 0  # number of times a "wtf" has occurred recently.
        # reset wtf's every 30 seconds 
        self.resetter = task.LoopingCall(self._resetWtfCount).start(30.0)
        self.sessions = []
        self.defaultSession = None
        # TODO - analyze, do i *really* need responding?
        self.responding = 0 # don't start responding until i'm in a channel
        # no irc.IRCClient.__init__ to call

    def findSession(self, channel):
        """Return the channel that matches channel, or the channel
        that has channel (a nick) in its list of people
        Otherwise return the defaultSession, usually indicating that someone
        has /msg'd the bot and that person is not in a channel with the bot.
        """
        for session in self.sessions:
            if channel == session.channel:
                return session
            if session.matchNick(channel):
                return session
        return self.defaultSession

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
            reactor.callLater(n*(delay/1000.0), send, line)

    def sendResponse(self, response):
        if response is None:
            return
        _already = []
        for channel, text in response.getMessages():
            # don't send messages to any users twice
            if channel in _already:
                continue

            print text
            splittext = text.splitlines()
            if len(splittext) > 1:
                self.msgSlowly(channel, splittext)
            else:
                self.msg(channel, text)
            _already.append(channel)

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
        self.defaultSession = d20session.D20Session('')
        # join my default channel
        self.join(self.factory.channel)

    def joined(self, channel):
        """When the bot joins a channel, find or make a session
        and start tracking who's in the session.
        """
        # find or make a session
        session = self.findSession(channel)
        if session is self.defaultSession: # i.e., not found
            session = d20session.D20Session(channel)
            self.sessions.append(session)

        self.responding = 1

    def left(self, channel):
        session = self.findSession(channel)
        self.sessions.remove(session)

    def kickedFrom(self, channel, kicker, message):
        session = self.findSession(channel)
        self.sessions.remove(session)

    def userJoined(self, user, channel):
        session = self.findSession(channel)
        self.sendResponse(session.addNick(user))

    def userLeft(self, user, channel):
        session = self.findSession(user)
        self.sendResponse(session.removeNick(user))

    def userQuit(self, user, quitmessage):
        session = self.findSession(user)
        self.sendResponse(session.removeNick(user))

    def userKicked(self, user, channel, kicker, kickmessage):
        session = self.findSession(user)
        self.sendResponse(session.removeNick(user))

    def userRenamed(self, old, new):
        session = self.findSession(old)
        self.sendResponse(session.rename(old, new))

    def irc_RPL_NAMREPLY(self, prefix, (user, _, channel, names)):
        nicks = names.split()
        for nick in nicks[:]:
            if nick[0] in '@+':
                nicks.remove(nick)
                nicks.append(nick[1:])

        session = self.findSession(channel)
        self.sendResponse(session.addNick(*nicks))

    def irc_RPL_ENDOFNAMES(self, prefix, params):
        pass

    def irc_unknown(self, prefix, command, params):
        log.msg('|||'.join((prefix, command, repr(params))))

    def irc_INVITE(self, prefix, (user, channel)):
        self.join(channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        log.msg(user, channel, msg)
        if not self.responding:
            return
        # Check to see if they're sending me a private message
        # If so, the return channel is the user.
        if channel == self.nickname:
            channel = user

        session = self.findSession(channel)

        parsed = linesyntax.parseSentence(msg)
        if parsed.command:
            if channel == user:
                response = session.privateCommand(user, parsed.command)
            else:
                response = session.command(user, parsed.command)
            self.sendResponse(response)
        elif parsed.verbPhrases:
            if channel == user:
                response = session.privateInteraction(user, msg, parsed)
            else:
                response = session.interaction(user, msg, parsed)
            self.sendResponse(response)
        else:
            pass

    # though it looks weird, actions will behave the same way as privmsgs.
    # for example, /me .hello will behave like "VellumTalk: hello" or ".hello"
    action = privmsg


class VellumTalkFactory(protocol.ClientFactory):
    """A factory for VellumTalks.

    A new protocol instance will be created each time we connect to the server.
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

