"""
Quick hack to make tests pass while I think about a real formatting interface
"""
import string

from zope.interface import Interface, implements, providedBy
from zope.interface.adapter import AdapterRegistry
from zope.interface.interface import adapter_hooks

from playtools.interfaces import IRuleFact
from playtools import query

from goonmill import history

from . import interface


class IOneLine(Interface):
    """
    An object which can be formatted as a single-line description
    """
    def format():
        """
        Return the one-line description as a unicode string
        """


def oneLineForSpell(spell):
    tmpl = string.Template('<<$name>> $school $subschool|| Level: $level || Casting Time: $time || $comps || Range: $range || $areaAndTarget || Duration: $duration $save|| $short || $url'
            )
    dct = {'name':spell.name,
            'school': spell.school,
            'level':spell.level,
            'time':spell.casting_time,
            'comps':''.join([s.strip() for s in spell.components.split(',')]),
            'range':spell.range,
            'duration':spell.duration,
            'short':spell.short_description,
            'url':query.srdReferenceURL(spell),
            }
    
    if spell.subschool:
        subschool = '(%s) ' % (spell.subschool,)
    else:
        subschool = ''

    if spell.area and spell.target:
        areaAndTarget = 'Area: %s || Target: %s' % (spell.area, spell.target)
    elif spell.target:
        areaAndTarget = 'Target: %s' % (spell.target,)
    elif spell.area:
        areaAndTarget = 'Area: %s' % (spell.area,)
    else:
        areaAndTarget = 'Target: (none)' 

    if spell.saving_throw:
        save = '|| Save: %s ' % (spell.saving_throw,)
    else:
        save = ''

    dct['areaAndTarget'] = areaAndTarget
    dct['subschool'] = subschool 
    dct['save'] = save
    return tmpl.safe_substitute(dct)


_ONELINE_MAPPING = {query.Monster: history.oneLineDescription,
        query.Spell: oneLineForSpell
        }


class OneLineDescriptor(object):
    __used_for__ = IRuleFact
    implements(IOneLine)

    def __init__(self, context):
        self.context = context

    def format(self):
        """
        Produce a single-line description suitable for pure-text environments
        """
        return _ONELINE_MAPPING[self.context.__class__](self.context)

registry = AdapterRegistry()
registry.register([IRuleFact], IOneLine, '', OneLineDescriptor)

def hook(provided, object):
    """
    For IFoo(bar), call an already-registered adapter to adapt bar to IFoo
    """
    adapter = registry.lookup1(providedBy(object), provided,
            '')
    return adapter(object)

adapter_hooks.append(hook)
