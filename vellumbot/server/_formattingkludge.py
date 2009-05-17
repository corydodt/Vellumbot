"""
Quick hack to make tests pass while I think about a real formatting interface
"""
import string

from zope.interface import Interface, implements, providedBy
from zope.interface.interface import adapter_hooks

from playtools.interfaces import IRuleCollection
from playtools import fact, globalRegistry
from playtools.plugins import d20srd35

from goonmill import statblock

from . import interface


SRD = fact.systems['D20 SRD']


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
            'url':d20srd35.srdReferenceURL(spell),
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


def oneLineForMonster(monster):
    """
    Produce a single-line description suitable for pure-text environments
    """
    sb = statblock.Statblock.fromMonster(monster)
    get = sb.get
    tmpl = string.Template(
            '<<$name>> $alignment $size $creatureType || Init $initiative || $senses Listen $listen Spot $spot || AC $ac || $hitDice HD || Fort $fort Ref $ref Will $will || $speed $attacks$attackOptions$spellLikes|| $abilities || SQ $SQ || $url')
    dct = {'name': get('name'),
           'alignment': get('alignment'),
           'size': get('size'),
           'creatureType': get('type'),
           'initiative': get('initiative'),
           'senses': get('senses'),
           'listen': get('listen'),
           'spot': get('spot'),
           'ac': get('armor_class'),
           'hitDice': get('hitDice'),
           'fort': get('fort'),
           'ref': get('ref'),
           'will': get('will'),
           'speed': get('speed'),
           'attacks': '',
           'attackOptions': '',
           'spellLikes': '',
           'abilities': get('abilities'),
           'SQ': get('special_qualities'),
           'url': d20srd35.srdReferenceURL(monster),
           }

    attacks = []
    attackGroups = sb.get('attackGroups')
    melees = attackGroups['melee']
    rangeds = attackGroups['ranged']
    for melee in melees:
        attacks.append("MELEE %s" % (melee,))
    for ranged in rangeds:
        attacks.append("RANGED %s" % (ranged,))
    if attacks:
        dct['attacks'] = '|| %s ' % (' '.join(attacks),)

    attackOptions = get('special_attacks')
    if attackOptions:
        dct['attackOptions'] = '|| Atk Options %s ' % (attackOptions,)

    spellLikes = get('spellLikeAbilities')
    if spellLikes:
        dct['spellLikes'] = '|| Spell-Like: %s ' % (spellLikes,)

    # resistance, immunity, spell resistance, and vulnerability are all
    # found in the SQ field already, so DRY

    return tmpl.safe_substitute(dct)


_ONELINE_MAPPING = {SRD.facts['monster'].klass: oneLineForMonster,
        SRD.facts['spell'].klass: oneLineForSpell
        }


class OneLineDescriptor(object):
    __used_for__ = d20srd35.IStormFact
    implements(IOneLine)

    def __init__(self, context):
        self.context = context

    def format(self):
        """
        Produce a single-line description suitable for pure-text environments
        """
        return _ONELINE_MAPPING[self.context.__class__](self.context)

globalRegistry.register([d20srd35.IStormFact], IOneLine, '', OneLineDescriptor)
