import sys
import string
import traceback

from zope.interface import Interface, implements

from twisted.python import log

from vellumbot.server import alias
from vellumbot.server.fs import fs


class UnknownHailError(Exception):
    pass


class ISessionResponse(Interface):
    """
    A source of messages to send to one or more channels, in response to a session
    action.
    """
    def getMessages():
        """
        @returns the messages as a list of 2-tuples: (recipient, message)
        """


class ResponseGroup(object):
    """
    A response that is built of other responses
    """
    implements(ISessionResponse)
    def __init__(self, *responses):
        self.responses = []
        for r in responses:
            self.addResponse(r)

    def addResponse(self, response):
        if ISessionResponse.providedBy(response):
            self.responses.append(response)
        else:
            self.responses.append(Response(*response))

    def getMessages(self):
        """
        Recurse through my responses to return messages
        """
        ret = []
        for res in self.responses:
            for m in res.getMessages():
                yield m


class Response(object):
    """A response vector with the channels the response should be sent to"""
    implements(ISessionResponse)
    def __init__(self, text, request, redirectTo=None):
        self.text = text
        self.context = request.message
        self.channel = request.recipients[0] 
        self.more_channels = request.recipients[1:]
        self.redirectTo = redirectTo

    def getMessages(self):
        """Generate messages to each channel"""
        if len(self.more_channels) > 0:
            text = self.text + ' (observed)'
            more_text = '%s (<%s>  %s)' % (self.text,
                                           self.channel,
                                           self.context)
        else:
            text = self.text

        if self.channel.startswith('#') and self.redirectTo is not None:
            yield (self.redirectTo, text)
        else:
            yield (self.channel, text)
        for ch in self.more_channels:
            yield (ch, more_text)


class Session:
    """
    A stateful channel, with game- and participant-specific knowledge that is
    remembered from one message to the next.
    """
    def __init__(self, channel):
        self.channel = channel
        # TODO - move this into d20-specific code somewhere
        self.initiatives = []
        self.nicks = set() # TODO - add a wrapper function for fixing bindings
                           # when nicks are removed or added
        self.observers = set()

    # responses to being hailed by a user
    def respondTo_DEFAULT(self, request, args):
        raise UnknownHailError()


    def respondTo_lookup(self, req, rest):
        """
        Set the speaker as the gm for this game session.
        """
        r = list(rest)
        what = r.pop(0)
        default = lambda u, r: "I don't know how to look those things up."
        return getattr(self, 'lookup_%s' % (what,), default)(req, r)

    def respondTo_gm(self, request, _):
        """
        Set the speaker as the gm for this game session.
        """
        self.observers.add(request.user)
        return ('%s is now a GM and will observe private '
                'messages for session %s' % (request.user, self.channel,))

    def respondTo_hello(self, request, _):
        """Greet the speaker."""
        return 'Hello %s.' % (request.user,)

    def respondTo_aliases(self, request, characters):
        """
        Show aliases for a character or for myself
        """
        if len(characters) == 0:
            characters.append(request.user)
        ret = []
        m = string.Template('Aliases for $char:   $formatted')
        for c in characters:
            d = {'char':c, 'formatted':alias.shortFormatAliases(c)}
            ret.append(m.safe_substitute(d))
        return '\n'.join(ret)

    def respondTo_unalias(self, request, removes):
        """Remove an alias from a character: unalias [character] <alias>"""
        if len(removes) > 1:
            key = removes[1]
            character = removes[0]
        else:
            key = removes[0]
            character = request.user

        removed = alias.removeAlias(key, character)
        if removed is not None:
            return "%s, removed your alias for %s" % (character, key)
        else:
            return "** No alias \"%s\" for %s" % (key, character)

    def respondTo_help(self, request, _):
        """This drivel."""
        _commands = []
        commands = []
        for att in dir(self):
            member = getattr(self, att)
            if (att.startswith('respondTo_')
                and callable(member)
                and att[10:].upper() != att[10:]):  # CAPITALIZED are reserved.
                _commands.append('%s: %s' % (att[10:], member.__doc__))

        _d = {'commands': '\n    '.join(_commands), }

        response = file(fs.help).read() % _d
        # TODO - don't ever send this to the channel
        return response

    def doInitiative(self, user, result):
        self.initiatives.append((result[0].sum(), user))
        self.initiatives.sort()
        self.initiatives.reverse()

    def matchNick(self, nick):
        """True if nick is part of this session."""
        return nick in self.nicks

    def privateInteraction(self, request):
        # if user is one of self.observers, we don't want to send another
        # reply.  make a set of the two bundles to filter out dupes.
        recipients = set([request.user] + list(self.observers))
        return self.doInteraction(request, *recipients)

    def interaction(self, request):
        return self.doInteraction(request, self.channel)

    def doInteraction(self, request, *recipients):
        """Use actor's stats to apply each action to all targets"""
        assert recipients, "interaction with no recipients"
        if request.sentence.actor:
            actor = request.sentence.actor
        else:
            actor = request.user

        strings = []
        for vp in request.sentence.verbPhrases:
            if vp.nonDiceWords is None:
                verbs = ()
            else:
                verbs = tuple(vp.nonDiceWords.split())
            if len(request.sentence.targets) == 0:
                formatted = alias.resolve(actor,    
                                          verbs,
                                          parsed_dice=vp.diceExpression,
                                          temp_modifier=vp.dieModifier)
                if formatted is not None:
                    strings.append(formatted)
            else:
                for target in request.sentence.targets:
                    formatted = alias.resolve(actor,
                                              verbs,
                                              parsed_dice=vp.diceExpression,
                                              temp_modifier=vp.dieModifier,
                                              target=target)
                    if formatted is not None:
                        strings.append(formatted)
        if strings:
            text = '\n'.join(strings)
            request.recipients = recipients
            return Response(text, request)

    def command(self, request):
        """Choose a method based on the command word, and pass args if any"""
        request.recipients = [self.channel]
        return self.doCommand(request)

    def privateCommand(self, request):
        request.recipients = list(set([request.user] + list(self.observers)))
        return self.doCommand(request)

    def doCommand(self, request):
        command = request.sentence.command
        m = self.getCommandMethod(command)

        try:
            response = m(request, request.sentence.commandArgs)
            if ISessionResponse.providedBy(response):
                return response
            return Response(response, request)
        except UnknownHailError, e:
            return Response("wtf?", request)
        except Exception, e:
            log.msg(''.join(traceback.format_exception(*sys.exc_info())))
            from . import session as myself
            if getattr(myself, 'TESTING', True):
                raise
            text = '** Sorry, %s: %s' % (request.user, str(e))
            return Response(text, request)

    def getCommandMethod(self, command):
        return getattr(self, 'respondTo_%s' % (command,),
                       self.respondTo_DEFAULT)

    def addNick(self, *nicks):
        self.nicks |= set(nicks)
        return self.reportNicks('Added %s' % (str(nicks),))

    def removeNick(self, *nicks):
        self.nicks ^= set(nicks)
        # also update self.observers
        self.observers ^= set(nicks)
        return self.reportNicks('Removed %s' % (str(nicks),))

    def reportNicks(self, why):
        nicks = ', '.join(self.nicks)
        return None # FIXME - very spammy when on
        return Response("Nicks in this session: %s" % (nicks,),
                        request)

    def rename(self, old, new):
        self.nicks -= set((old,))
        self.nicks |= set((new,))
        # also update self.observers
        if old in self.observers:
            self.observers -= set((old,))
            self.observers |= set((new,))
        # TODO - rename old's aliases so they work for new
        return self.reportNicks('%s renamed to %s' % (old, new))

