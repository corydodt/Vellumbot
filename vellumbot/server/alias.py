"""A table of aliases."""
try:
    import cPickle as pickle
except ImportError:
    import pickle

from playtools import dice
from playtools.parser import diceparser

_alias_hooks = {}

def registerAliasHook(alias, hook):
    """Register a handler for a particular alias.  Handlers must
    take two arguments, username and evaluated result.

    # def rememberInitiative(user, initroll):
    # ....iniatives.append((initroll, user))
    # >>> addAliasHook(('init',), rememberInitiative)

    Now rememberInitiative will get called any time someone uses "[init ..]"
    """
    _alias_hooks.setdefault(alias, []).append(hook)

def shortFormatAliases(user):
    """
    Return all the aliases for user in a short format
    """
    my_aliases = user.getAliases()
    if len(my_aliases) == 0:
        return '(none)'
    formatted_aliases = []
    alias_items = my_aliases.items()
    alias_items.sort()
    for key, value in alias_items:
        formatted_aliases.append('%s=%s' % (key, value))
    return ', '.join(formatted_aliases)

def resolve(actor, words, parsed_dice=None, temp_modifier=0, target=None):
    """
    If there is a known alias or a dice expression in there, return the
    message result from processing it.

    If neither a known alias nor a dice expression, return None.
    """
    rolled = getResult(actor, words, parsed_dice, temp_modifier, target=target)
    if rolled is None:
        return None
    else:
        return formatAlias(actor.name, words, rolled, parsed_dice, temp_modifier)

def callAliasHooks(words, user, rolled):
    """
    After rolling an alias, do the hooks
    """
    hooks = _alias_hooks.get(words, [])
    for hook in hooks:
        hook(user, rolled)

def getResult(actor, words, parsed_dice=None, temp_modifier=0, target=None):
    """
    Return a list of dice result
    """
    # targets - TODO
    parse = diceparser.parseDice
    unparse = lambda x: x.format()

    # verb phrases with dice expressions set a new expression
    if parsed_dice is not None:
        if words:
            actor.setAlias(words, unparse(parsed_dice))
    else: # without dice expression, look it up or regard it as empty
        _dict = actor.getAliases()
        looked_up = _dict.get(' '.join(words), None)
        if looked_up is None:
            parsed_dice = None
        else:
            parsed_dice = parse(looked_up)

    if parsed_dice is None:
        rolled = None
    else:
        rolled = list(dice.roll(parsed_dice, temp_modifier))
    callAliasHooks(words, actor, rolled)
    return rolled

def formatAlias(actor, verbs, results, parsed_dice, temp_modifier=0, target=None):
    """
    Return the result of rolling some dice as an irc message
    """
    assert target is None
    assert type(verbs) is tuple, '%r is not tuple' % (verbs,)
    verbs = list(verbs)
    sorted = 0 
    if parsed_dice is None or parsed_dice == '':
        pass
    else:
        verbs.append(str(parsed_dice))
        # use 'sort' token to decide whether to sort now
        if parsed_dice.sort:
            results.sort()
            sorted = 1
    if temp_modifier:
        verbs.append('%+d' % (temp_modifier,))

    
    rolls = '[%s]' % (', '.join([r.format() for r in results]))
    if sorted:
        rolls = rolls + ' (sorted)'
    return '%s, you rolled: %s = %s' % (actor, ' '.join(verbs), rolls)

