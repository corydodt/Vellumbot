import sys
import string
import traceback

from zope.interface import implements

from twisted.python import log

from storm import locals as L

from . import alias
from .fs import fs
from ..user import User
from .interface import IMessageRecipient, ISessionResponse


class UnknownHailError(Exception):
    """
    The bot saw something that looked like a command, but could not figure out
    how to run the command.
    """


class MissingRecipients(Exception):
    """
    An attempt was made to create a response to a request, but nobody told me
    what the recipients would be.  (Call request.setRecipients() first.)
    """


class ResponseGroup(object):
    """
    A response that is built of other responses.  This represents a series of
    different (related) messages sent to one or more people.
    """
    implements(ISessionResponse)
    def __init__(self, *responses):
        self.responses = []
        for r in responses:
            self.addResponse(r)

    def addResponse(self, response):
        assert ISessionResponse.providedBy(response), "%r is not a ISessionResponse" % (response,)
        self.responses.append(response)

    def getMessages(self):
        """
        Recurse through my responses to return messages
        """
        ret = []
        for res in self.responses:
            for m in res.getMessages():
                yield m


class Response(object):
    """
    A response vector with the channels the response should be sent to.  This
    usually represents a single message, sent simultaneously to many people.
    """
    implements(ISessionResponse)
    def __init__(self, text, request, redirectTo=None):
        self.text = text
        assert text, "response text is blank!"
        self.context = request.message
        if request.recipients is None:
            raise MissingRecipients(
                    "call request.setRecipients() before constructing a Response")
        self.channel = request.recipients[0] 
        assert self.channel.name, "response channel is %r" % (self.channel,)
        self.request = request
        self.more_channels = request.recipients[1:]
        assert (IMessageRecipient.providedBy(redirectTo) or 
                type(redirectTo) is type(None)
                ), "%r is not a Session!" % (redirectTo,)
        self.redirectTo = redirectTo

    def getMessages(self):
        """Generate messages to each channel"""
        if len(self.more_channels) > 0:
            text = self.text + ' (observed)'
            more_text = '<%s>  %s  ===>  %s' % (
                                           self.request.user,
                                           self.context,
                                           self.text,)
        else:
            text = self.text

        assert text, "message text is blank"
        if self.channel.name.startswith(u'#') and self.redirectTo is not None:
            yield (self.redirectTo, text, self.redirectTo.encoding)
        else:
            assert IMessageRecipient.providedBy(self.channel), "self.channel is not a IMessageRecipient!"
            yield (self.channel, text, self.channel.encoding)
        for ch in self.more_channels:
            assert IMessageRecipient.providedBy(ch), "ch is not a IMessageRecipient!"
            yield (ch, more_text, ch.encoding)


class Session(object):
    """
    A stateful channel, with game- and participant-specific knowledge that is
    remembered from one message to the next.
    """
    __storm_table__ = 'session'
    name = L.Unicode(primary=True)
    encoding = L.Unicode(default=u'utf-8')

    implements(IMessageRecipient)

    def __init__(self, isDefaultSession=False):
        self.subSessions = set()  # TODO - add a wrapper function for fixing 
                                  # bindings when nicks are removed or added
        self.observers = set()
        self.isDefaultSession = isDefaultSession

    __storm_loaded__ = __init__

    def __repr__(self):
        return "<Session %s>" % (self.name,)

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    # responses to being hailed by a user
    def respondTo_DEFAULT(self, request, actor, args):
        raise UnknownHailError()

    def respondTo_lookup(self, req, actor, rest):
        """
        Do a search and report results found
        """
        r = list(rest)
        what = r.pop(0)
        default = lambda u, r: "I don't know how to look those things up."
        return getattr(self, 'lookup_%s' % (what,), default)(req, r)

    def respondTo_gm(self, request, actor, _):
        """
        Set the speaker as the gm for this game session.
        """
        self.observers.add(self._nameToRecipient(actor.name))
        return (u'%s is now a GM and will observe private messages for session %s' % (
            actor.name, self.name,))

    def respondTo_hello(self, request, actor, _):
        """Greet the speaker."""
        return 'Hello %s.' % (actor.name,)

    def respondTo_aliases(self, request, actor, characters):
        """
        Show aliases for a character or for myself
        """
        if len(characters) == 0:
            characters.append(actor)
        else:
            # FIXME - should be able to do this with one query
            characters = map(self._nameToUser, characters)
        ret = []
        m = string.Template(u'Aliases for $char:   $formatted')
        for c in characters:
            d = {'char':c.name, 'formatted': alias.shortFormatAliases(c)}
            ret.append(m.safe_substitute(d))
        return u'\n'.join(ret)

    def respondTo_unalias(self, request, actor, removes):
        """Remove an alias from a character: unalias [character] <alias>"""
        if len(removes) > 1:
            key = removes[1]
            character = self._nameToUser(removes[0])
        else:
            key = removes[0]
            character = actor

        removed = character.removeAlias(key)
        if removed is not None:
            return u"%s, removed your alias for %s" % (character.name, key)
        else:
            return u"** No alias \"%s\" for %s" % (key, character.name)

    def respondTo_help(self, request, actor, _):
        """
        This drivel.
        """
        _commands = []
        commands = []
        for att in dir(self):
            member = getattr(self, att)
            if (att.startswith('respondTo_')
                and callable(member)
                and att[10:].upper() != att[10:]):  # CAPITALIZED are reserved.
                _commands.append(u'%s: %s' % (att[10:],
                    member.__doc__.decode(self.encoding)))

        _d = {'commands': u'\n    '.join(_commands), }

        response = file(fs.help).read() % _d
        # TODO - don't ever send this to the channel
        return response

    def matchNick(self, nick):
        """True if nick is part of this session."""
        assert type(nick) is unicode
        return nick.lower() in map(unicode.lower, [n.name for n in self.subSessions])

    def privateInteraction(self, request, *observers):
        # if user is one of self.observers, we don't want to send another
        # reply.  make a set of the two bundles to filter out dupes.
        assert type(request.user) is unicode
        assert (not observers) or [o for o in observers if type(o) is unicode]
        others = set(observers)
        if request.user in others:
            others.remove(request.user)
        ## TODO _ request.setRecipients(request.user, *others)
        return self.doInteraction(request, request.user, *others)

    def interaction(self, request):
        assert not self.isDefaultSession
        return self.doInteraction(request, self.name)

    def doInteraction(self, request, *recipients):
        """Use actor's stats to apply each action to all targets"""
        assert [r for r in recipients if r], "interaction with recipients=%r" % (recipients,)
        assert not [r for r in recipients if type(r) is not unicode], "Not all recipients were unicode"
        recipients = list(recipients)

        createActorNeeded = False       # set to True when we are dealing with
                                        # a nick hijacking i.e. *Hamlet [stabs] you

        if request.sentence.actor:
            _actor = request.sentence.actor
            createActorNeeded = True
        else:
            _actor = request.user

        # associate the name with a user in the database
        actor = self._nameToUser(_actor, createActorNeeded)

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
                assert type(formatted) in [unicode, type(None)], "formatted is %r" % (formatted,)
                if formatted is not None:
                    strings.append(formatted)
            else:
                for target in request.sentence.targets:
                    formatted = alias.resolve(actor,
                                              verbs,
                                              parsed_dice=vp.diceExpression,
                                              temp_modifier=vp.dieModifier,
                                              target=target)
                    assert type(formatted) is unicode
                    if formatted is not None:
                        strings.append(formatted)
        if strings:
            text = u'\n'.join(strings)
            for n, r in enumerate(recipients):
                recipients[n] = self._nameToRecipient(r)

            assert [IMessageRecipient.providedBy(r) for r in recipients]
            request.setRecipients(*recipients)
            return Response(text, request)

    def command(self, request):
        """Choose a method based on the command word, and pass args if any"""
        assert IMessageRecipient.providedBy(self)
        request.setRecipients(self)
        return self.doCommand(request)

    def _nameToRecipient(self, name):
        """
        Return an appropriate IMessageRecipient for the given name
        """
        name = name.decode(self.encoding)
        if name == self.name:
            ss = self
        elif name.startswith(u'#'):
            # TODO - we probably never reach here with current code.
            # this is if a bot wants to say something in more than
            # one public channel, which I don't think is possible.
            ss = Store.of(self).find(Session, Session.name == name).one()
        else:
            ss = User()
            ss.name = name 
        assert IMessageRecipient.providedBy(ss)
        return ss

    def _nameToUser(self, name, createFlag=False):
        """
        An appropriate User object for the given name

        If createFlag == True we are allowed to create the actor, i.e. this
        was a nick hijacking and this person is possibly artificial
        """
        store = L.Store.of(self)
        ret = store.find(User,
                User.name.like(name, case_sensitive=False)).one()
        if ret is None:
            if createFlag:
                ret = User()
                ret.name = name
                store.add(ret)
                store.commit()
        assert ret is not None, "Actor %r did not exist and was not created." % (name,)
        return ret

    def privateCommand(self, request, *observers):
        assert type(request.user) is unicode
        assert (not observers) or [o for o in observers if type(o) is unicode]

        observers = list(observers)
        if request.user in observers:
            observers.remove(request.user)

        others = set(self._nameToRecipient(o) for o in observers)
        request.setRecipients(self._nameToRecipient(request.user), *others)
        return self.doCommand(request)

    def doCommand(self, request):
        command = request.sentence.command
        assert type(command) is unicode
        m = self.getCommandMethod(command)

        # associate the name with a user in the database
        actor = self._nameToUser(request.user)

        try:
            response = m(request, actor, request.sentence.commandArgs)
            if ISessionResponse.providedBy(response):
                return response
            return Response(response, request)
        except UnknownHailError, e:
            return Response(u"wtf?", request)
        except Exception, e:
            log.msg(''.join(traceback.format_exception(*sys.exc_info())))
            from . import session as myself
            if getattr(myself, 'TESTING', True):
                raise
            text = u'** Sorry, %s: %s' % (request.user,
                    e.decode(self.encoding))
            return Response(text, request)

    def getCommandMethod(self, command):
        return getattr(self, 'respondTo_%s' % (command,),
                       self.respondTo_DEFAULT)

    def addNick(self, *nicks):
        """
        Add a nick to the session list, and make sure that nick is known in
        the database as a User object, too
        """
        assert [n for n in nicks if type(n) is unicode]
        self.subSessions |= set(self._nameToRecipient(n) for n in nicks)
        store = L.Store.of(self)
        for nick in nicks:
            user = L.Store.of(self).find(User, User.name.like(nick,
                case_sensitive=False)).one()
            if user is None:
                u = User()
                u.name = nick
                store.add(u)
        store.commit()
        nicks = u', '.join(nicks)
        return self.reportNicks(u'Added %s' % (nicks,))

    def removeNick(self, *nicks):
        assert [n for n in nicks if type(n) is unicode]
        self.subSessions -= set(self._nameToRecipient(n) for n in nicks)
        # also update self.observers
        toRemove = [self._nameToRecipient(n) for n in nicks]
        self.observers -= set(toRemove)
        nicks = u', '.join(nicks)
        return self.reportNicks(u'Removed %s' % (nicks,))

    def reportNicks(self, message):
        assert type(message) is unicode
        return None # FIXME - very spammy when on
        return Response(u"Nicks in this session: %s" % (nicks,),
                        request)

    def rename(self, old, new):
        assert type(old) is type(new) is unicode

        _new = self._nameToUser(new, True)
        _old = self._nameToUser(old)

        assert _old is not None, "strangely, attempting to remove user %r who does not exist" % (old,)
        assert _new is not None, "strangely, user %r did not exist and was not created" % (new,)

        store = L.Store.of(self)
        store.remove(_old)
        store.commit()

        self.subSessions -= set((_old,))
        self.subSessions |= set((_new,))
        # also update self.observers
        if _old in self.observers:
            self.observers -= set((_old,))
            self.observers |= set((_new,))
        # TODO - rename old's aliases so they work for new
        return self.reportNicks(u'%s renamed to %s' % (old, new))

