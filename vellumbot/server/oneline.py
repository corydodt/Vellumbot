"""
Quick hack to make tests pass while I think about a real formatting interface
"""
import string

from zope.interface import implements

from playtools import fact, publish
from playtools.interfaces import IPublisher
from playtools.plugins import d20srd35
from playtools.search import textFromHtml

from goonmill import statblock


SRD = fact.systems['D20 SRD']


class OneLineSpellPublisher(object):
    implements(IPublisher)
    name = 'oneLine'
    tmpl = string.Template('<<$name>>   $school $subschool|| Level: $level || Casting Time: $time || $comps || Range: $range || $areaAndTarget || Duration: $duration $save|| $short || $url')
    def format(self, spell):
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
        return self.tmpl.safe_substitute(dct)

class RichIRCSpellPublisher(OneLineSpellPublisher):
    implements(IPublisher)
    name = 'richIRC'
    tmpl = string.Template('\037$name\017   $school $subschool|| Level: $level || Casting Time: $time || $comps || Range: $range || $areaAndTarget || Duration: $duration $save|| \002$short\017 || $url')

publish.addPublisher(SRD.facts['spell'], OneLineSpellPublisher)
publish.addPublisher(SRD.facts['spell'], RichIRCSpellPublisher)


class OneLineMonsterPublisher(object):
    implements(IPublisher)
    name = 'oneLine'
    tmpl = string.Template(
            '<<$name>>   $alignment $size $creatureType || Init $initiative || $senses Listen $listen Spot $spot || AC $ac || $hitDice HD || Fort $fort Ref $ref Will $will || $speed $attacks$attackOptions$spellLikes|| $abilities || SQ $SQ || $url')
    def format(self, monster):
        """
        Produce a single-line description suitable for pure-text environments
        """
        sb = statblock.Statblock.fromMonster(monster)
        get = sb.get
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

        return self.tmpl.safe_substitute(dct)

class RichIRCMonsterPublisher(OneLineMonsterPublisher):
    implements(IPublisher)
    name = 'richIRC'
    tmpl = string.Template(
            '\037$name\017   $alignment $size $creatureType || Init \002$initiative\017 || $senses Listen $listen Spot $spot || AC \002$ac\017 || $hitDice HD || Fort $fort Ref $ref Will $will || $speed \002$attacks\017$attackOptions$spellLikes|| $abilities || SQ $SQ || $url')

publish.addPublisher(SRD.facts['monster'], OneLineMonsterPublisher)
publish.addPublisher(SRD.facts['monster'], RichIRCMonsterPublisher)


class OneLineSkillPublisher(object):
    implements(IPublisher)
    name = 'oneLine'
    tmpl = string.Template(
            '<<$name>>   Key Ability: $keyAbil || Action: $action || Try Again? $tryAgain || $url')
    def format(self, skill):
        """
        Produce a single-line description suitable for pure-text environments
        """
        keyAbil = unicode(skill.keyAbility.label)
        action = unicode(skill.skillAction)
        tryAgain = unicode(skill.tryAgainComment) or u'yes'
        url = unicode(skill.reference.resUri)
        dct = {'name': unicode(skill.label),
                'keyAbil': keyAbil,
                'action': action,
                'tryAgain': tryAgain,
                'url': url,
                }

        return self.tmpl.safe_substitute(dct)

class RichIRCSkillPublisher(OneLineSkillPublisher):
    implements(IPublisher)
    name = 'richIRC'
    tmpl = string.Template(
            '\037$name\017   Key Ability: $keyAbil || Action: $action || Try Again? $tryAgain || $url')

publish.addPublisher(SRD.facts['skill'], OneLineSkillPublisher)
publish.addPublisher(SRD.facts['skill'], RichIRCSkillPublisher)


class OneLineFeatPublisher(object):
    implements(IPublisher)
    name = 'oneLine'
    tmpl = string.Template(
            '<<$name>>   $benefit || $url')
    def format(self, feat):
        """
        Produce a single-line description suitable for pure-text environments
        """
        benefit = unicode(feat.benefit)
        url = unicode(feat.reference.resUri)
        dct = {'name': unicode(feat.label),
                'benefit': textFromHtml(benefit),
                'url': url,
                }

        return self.tmpl.safe_substitute(dct)

class RichIRCFeatPublisher(OneLineFeatPublisher):
    implements(IPublisher)
    name = 'richIRC'
    tmpl = string.Template(
            '\037$name\017   $benefit || $url')

publish.addPublisher(SRD.facts['feat'], OneLineFeatPublisher)
publish.addPublisher(SRD.facts['feat'], RichIRCFeatPublisher)
