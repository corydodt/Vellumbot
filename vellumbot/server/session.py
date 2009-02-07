import sys
import string
import traceback
from sets import Set

from twisted.python import log

from vellumbot.server import alias
from vellumbot.server.fs import fs
import vellumbot


class UnknownHailError(Exception):
    pass

class Response(object):
    """A response vector with the channels the response should be sent to"""
    def __init__(self, text, context, channel, *channels):
        self.text = text
        self.context = context
        self.channel = channel
        self.more_channels = channels

    def getMessages(self):
        """Generate messages to each channel"""
        if len(self.more_channels) > 0:
            text = self.text + ' (observed)'
            more_text = '%s (<%s>  %s)' % (self.text,
                                           self.channel,
                                           self.context)
        else:
            text = self.text

        yield (self.channel, text)
        for ch in self.more_channels:
            yield (ch, more_text)

class Session:
    def __init__(self, channel):
        self.channel = channel
        # TODO - move this into d20-specific code somewhere
        self.initiatives = []
        self.nicks = Set() # TODO - add a wrapper function for fixing bindings
                           # when nicks are removed or added
        self.observers = Set()

    # responses to being hailed by a user
    def respondTo_DEFAULT(self, user, args):
        raise UnknownHailError()


    def respondTo_gm(self, user, _):
        self.observers.add(user)
        return ('%s is now a GM and will observe private '
                'messages for session %s' % (user, self.channel,))

    def respondTo_hello(self, user, _):
        """Greet."""
        return 'Hello %s.' % (user,)

    def respondTo_aliases(self, user, characters):
        """
        Show aliases for a character or for myself
        """
        if len(characters) == 0:
            characters.append(user)
        ret = []
        m = string.Template('Aliases for $char:   $formatted')
        for c in characters:
            d = {'char':c, 'formatted':alias.shortFormatAliases(c)}
            ret.append(m.safe_substitute(d))
        return '\n'.join(ret)

    def respondTo_unalias(self, user, removes):
        """Remove an alias from a character: unalias [character] <alias>"""
        if len(removes) > 1:
            key = removes[1]
            character = removes[0]
        else:
            key = removes[0]
            character = user

        removed = alias.removeAlias(key, character)
        if removed is not None:
            return "%s, removed your alias for %s" % (character, key)
        else:
            return "** No alias \"%s\" for %s" % (key, character)

    def respondTo_help(self, user, _):
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
        return response

    def doInitiative(self, user, result):
        self.initiatives.append((result[0].sum(), user))
        self.initiatives.sort()
        self.initiatives.reverse()

    def matchNick(self, nick):
        """True if nick is part of this session."""
        return nick in self.nicks

    def privateInteraction(self, user, msg, parsed):
        # if user is one of self.observers, we don't want to send another
        # reply.  make a set of the two bundles to filter out dupes.
        recipients = Set([user] + list(self.observers))
        return self.doInteraction(user, msg, parsed, *recipients)

    def interaction(self, user, msg, sentence):
        return self.doInteraction(user, msg, sentence, self.channel)

    def doInteraction(self, user, msg, sentence, *recipients):
        """Use actor's stats to apply each action to all targets"""
        assert recipients, "interaction with no recipients"
        if sentence.actor:
            actor = sentence.actor
        else:
            actor = user

        strings = []
        for vp in sentence.verbPhrases:
            if vp.nonDiceWords is None:
                verbs = ()
            else:
                verbs = tuple(vp.nonDiceWords.split())
            if len(sentence.targets) == 0:
                formatted = alias.resolve(actor,    
                                          verbs,
                                          parsed_dice=vp.diceExpression,
                                          temp_modifier=vp.dieModifier)
                if formatted is not None:
                    strings.append(formatted)
            else:
                for target in sentence.targets:
                    formatted = alias.resolve(actor,
                                              verbs,
                                              parsed_dice=vp.diceExpression,
                                              temp_modifier=vp.dieModifier,
                                              target=target)
                    if formatted is not None:
                        strings.append(formatted)
        if strings:
            text = '\n'.join(strings)
            return Response(text, msg, *recipients)

    def command(self, user, command):
        """Choose a method based on the command word, and pass args if any"""
        return self.doCommand(user, command, self.channel)

    def privateCommand(self, user, command):
        return self.doCommand(user, command, user, *self.observers)

    def doCommand(self, user, command, *recipients):
        m = self.getCommandMethod(command)

        context = command

        try:
            text = m(user, command.commandArgs)
            return Response(text, context, *recipients)
        except UnknownHailError, e:
            return Response("wtf?", context, *recipients)
        except Exception, e:
            log.msg(''.join(traceback.format_exception(*sys.exc_info())))
            from . import session as myself
            if getattr(myself, 'TESTING', True):
                raise
            text = '** Sorry, %s: %s' % (user, str(e))
            return Response(text, context, *recipients)

    def getCommandMethod(self, sentence):
        name = sentence.command
        return getattr(self, 'respondTo_%s' % (name,),
                       self.respondTo_DEFAULT)

    def addNick(self, *nicks):
        self.nicks |= Set(nicks)
        return self.reportNicks('Added %s' % (str(nicks),))

    def removeNick(self, *nicks):
        self.nicks ^= Set(nicks)
        # also update self.observers
        self.observers ^= Set(nicks)
        return self.reportNicks('Removed %s' % (str(nicks),))

    def reportNicks(self, why):
        nicks = ', '.join(self.nicks)
        return None # FIXME - very spammy when on
        return Response("Nicks in this session: %s" % (nicks,),
                        why,
                        self.channel)

    def rename(self, old, new):
        self.nicks -= Set((old,))
        self.nicks |= Set((new,))
        # also update self.observers
        if old in self.observers:
            self.observers -= Set((old,))
            self.observers |= Set((new,))
        # TODO - rename old's aliases so they work for new
        return self.reportNicks('%s renamed to %s' % (old, new))

