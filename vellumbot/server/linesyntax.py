r"""Define the syntax for parsing statements on IRC.
Lines may contain the following syntax:
    - A message that begins with the bot's name or begins with a dot
      is a structured command (beginning on the first token after the bot's
      name, if present), and it may take arguments.
    - A single word beginning with a letter and prefixed by a * anywhere in
      the line is the name of an actor.  There may be only one at most.
    - An expression inside brackets [] is a verb.
    - A verb starts with zero or more verbnames, and ends with an optional dice
      expression.
    - A dice expression
    - A target starts with @ and there may be more than one.
"""

import re
import shlex

from simpleparse import parser, dispatchprocessor as disp
from simpleparse.error import ParserSyntaxError
from simpleparse.common import numbers # importing for side effect
numbers # shut up pyflakes
from playtools import diceparser

grammar = ( # {{{
r'''# irc bot commands and recognized sentences
<ws>                    := [ \t]*
<identifier>            := [a-zA-Z], [a-zA-Z0-9_]*

<commandLeader>         := '.'
commandIdentifier       := identifier

botname                 := identifier

<hail>                  := botname, ws, (':'/','), ws

<CHAR>                  := -[[]/'['  

commandArgs             := CHAR+ 

command                 := (hail/commandLeader), ws, !, commandIdentifier, ([ \t]+, commandArgs)?, ws

commandRoot             := ws,command

<word>                  := [a-zA-Z0-9{}\/';":.,!@#$%^&*()-=_+]+  
nonDiceWords            := (?-(diceExpression),word,ws)+  

>diceExpressionAlone<   := diceExpression
>aliasAlone<            := nonDiceWords
>aliasPlusModifier<     := nonDiceWords, dieModifier
>aliasPlusExpression<   := nonDiceWords, diceExpression  

# order matters in vContent - most specific to most general
>vContent<              := diceExpressionAlone/aliasPlusModifier/aliasPlusExpression/aliasAlone

>verbPhrase<            := '[', !, vContent, ']'

verbPhraseRoot          := ws,verbPhrase



# you could say:
# word word *actor word word [verbs]
# or
# word word [verbs] word word *actor
# or
# word word [verbs] word word
# or
# word word [verbs]
# or
# [verbs]
# or
# word word

words                   := (word,ws)+  

nonCommand              := ?-(command),CHAR*

>sentence<              := command/nonCommand
sentenceRoot            := ws,sentence
''') # }}}

# do a half-assed parse with re to eliminate any non-syntax from a person's
# sentence.
verbsMaybe = re.compile(r'\[[^]]*\]')
target = re.compile(r'@[a-zA-Z][a-zA-Z0-9_]*')
actor = re.compile(r'\*[a-zA-Z][a-zA-Z0-9_]*')


class CommandProcessor(disp.DispatchProcessor):
    commandArgsFound = None
    commandName = None
    botName = None

    def commandIdentifier(self, (t,s1,s2,sub), buffer):
        disp.dispatchList(self, sub, buffer)
        self.commandName = buffer[s1:s2]

    def commandArgs(self, (t,s1,s2,sub), buffer):
        self.commandArgsFound = buffer[s1:s2]

    def command(self, (t,s1,s2,sub), buffer):
        disp.dispatchList(self, sub, buffer)
        return self.botName, self.commandName, self.commandArgsFound

    def botname(self, (t,s1,s2,sub), buffer):
        self.botName = buffer[s1:s2].lower()

def parseCommand(s):
    commandParser = parser.Parser(grammar, root="commandRoot")
    succ, children, end = commandParser.parse(s, processor=CommandProcessor())
    if not succ or not end == len(s):
        raise RuntimeError('%s is not a command' % (s,))
    return children



class Sentence(object):
    def __init__(self):
        self.diceExpression = None
        self.botName = None
        self.command = None
        self._commandArgs = []
        self.actor = None
        self.verbPhrases = []
        self.targets = []

    def get_commandArgs(self):
        return self._commandArgs

    def set_commandArgs(self, s):
        # blah - shlex.split(None) blocks waiting for input, so protect it
        self._commandArgs = shlex.split(s or '')

    commandArgs = property(get_commandArgs, set_commandArgs)

    def __repr__(self):
        return '<Sentence %s>' % (str(self),)

    def __str__(self):
        if self.command:
            ret = ['.', self.command]
            for ca in self.commandArgs:
                ret.append(' ')
                if ' ' in ca or '\t' in ca:
                    ca = '"' + ca.replace('"', '\"') + '"'
                ret.append(ca)
            return ''.join(ret)

        ret = []
        a = ret.append
        if self.actor:
            a("*%s does " % (self.actor,))
        if len(self.verbPhrases) == 0:
            a("***** missing verb phrase *****")
        else:
            for verbPhrase in self.verbPhrases:
                a("[%s]" % (verbPhrase,))

        if self.targets:
            a(" to @%s" % (self.targets.pop(0),))
        for target in self.targets:
            a(" and @%s" % (target,))
        a(".")

        return ''.join(ret)


class SentenceProcessor(CommandProcessor):
    def nonCommand(self, (t,s1,s2,sub), buffer):
        return buffer

def parseSentence(s):
    sp = SentenceProcessor()
    sent = Sentence()
    sentenceParser = parser.Parser(grammar, root="sentenceRoot")
    succ, children, end = sentenceParser.parse(s, processor=sp)
    if not succ or not end == len(s):
        # this might happen if you start with something that looks like a
        # command but isn't
        raise RuntimeError('%s is not a sentence' % (s,))

    if sp.commandName:
        sent.botName = sp.botName
        sent.command = sp.commandName
        sent.commandArgs = sp.commandArgsFound
        return sent
    else:
        actors = actor.findall(children[0])
        if len(actors) > 1:
            raise RuntimeError('Too many actors (only one allowed): %s' %
                    (actors,))
        elif len(actors) == 1:  
            sent.actor = actors[0][1:]

        verbCandidates = verbsMaybe.findall(children[0])
        for vc in verbCandidates:
            try:
                sent.verbPhrases.append(parseVerbPhrase(vc))
            except (RuntimeError, ParserSyntaxError):
                continue # it's not an error to have something that looks like
                         # a verb phrase but isn't.  Parse the ones we have,
                         # and make sure there's at least one ...
        if len(sent.verbPhrases) == 0:
            raise RuntimeError('No verb phrase or command')

        for t in target.findall(children[0]):
            sent.targets.append(t[1:])

        return sent


class VerbPhrase(object):
    dieModifier = None
    diceExpression = None
    nonDiceWords = None
    def __repr__(self):
        return '<Sentence %s>' % (str(self),)

    def __str__(self):  
        ret = []
        a = ret.append
        if self.nonDiceWords:
            a(self.nonDiceWords)
        if self.dieModifier:
            if self.nonDiceWords:
                a(' ')
            a('%+d' % (self.dieModifier,))
        if self.diceExpression:
            if self.nonDiceWords:
                a(' ')
            a(str(self.diceExpression))
        return ''.join(ret)


class VerbPhraseProcessor(disp.DispatchProcessor):
    def __init__(self, *a, **kw):
        # disp.DispatchProcessor.__init__(self, *a, **kw)
        self.verbPhrase = VerbPhrase()

    def diceExpression(self, (t,s1,s2,sub), buffer):
        self.verbPhrase.diceExpression = diceparser.parseDice(buffer[s1:s2])

    def nonDiceWords(self, (t,s1,s2,sub), buffer):
        b = buffer[s1:s2]
        self.verbPhrase.nonDiceWords = ' '.join(b.split()).lower()

    def dieModifier(self, (t,s1,s2,sub), buffer):
        self.verbPhrase.dieModifier = int(buffer[s1:s2])

def parseVerbPhrase(s):
    verbPhraseParser = parser.Parser(grammar, root="verbPhraseRoot")
    proc = VerbPhraseProcessor()
    succ, children, end = verbPhraseParser.parse(s, processor=proc)
    if not succ or not end == len(s):
        raise RuntimeError('%s is not a verb phrase' % (s,))
    return proc.verbPhrase

