from twisted.trial import unittest
import re

from . import util
from ..server import reference

class ReferenceTestCase(unittest.TestCase, util.DiffTestCaseMixin):
    """
    Test lookups and references
    """
    def test_findExactOne(self):
        """
        Searching of spell database works: exact match one word
        """
        ret = reference.find(u'spell', [u'fireball'])
        self.assertNoRxDiff(
                [re.escape('EXACT: \037Fireball\037   Evocation || Level: Sorcerer/Wizard 3 || Casting Time: 1 standard action || VSM || Range: Long (400 ft. + 40 ft./level) || Area: 20-ft. -radius spread || Duration: Instantaneous || Save: Reflex half || \0021d6 damage per level, 20-ft. radius.\002 || http://www.d20srd.org/srd/spells/fireball.htm'),
                    ],
                ret,
                'expected (regex)', 'actual')

    def test_findExactMultiple(self):
        """
        Searching of spell database works: exact match multiple words
        """
        ret = reference.find(u'spell', [u'cure serious wounds mass'])
        self.assertNoRxDiff(
                [re.escape('EXACT: \037Cure Serious Wounds, Mass\037   Conjuration (Healing) || Level: Cleric 7, Druid 8 || Casting Time: 1 standard action || VS || Range: Close (25 ft. + 5 ft./2 levels) || Target: One creature/level, no two of which can be more than 30 ft. apart || Duration: Instantaneous || Save: Will half (harmless) or Will half; see text || \002Cures 3d8 damage +1/level for many creatures.\002 || http://www.d20srd.org/srd/spells/cureSeriousWoundsMass.htm'),
                    ],
                ret,
                'expected (regex)', 'actual')

    def test_findNonExact(self):
        """
        Check that the searching of spell database works: non-exact match
        """
        ret = reference.find(u'spell', [u'cure'])
        self.assertEqual(len(ret), 5)
        self.assertNoRxDiff(
                [ur'"cure light wounds mass": \*\*Cure\*\* Light Wounds, Mass Conjuration.*, mass.*\.\.\.', 
                ur'.*', ur'.*', ur'.*', ur'.*'],
                ret,
                'expected (regex)', 'actual')

    def test_findExactSpecialCharacters(self):
        """
        Searching of spell database works: match spells with special
        characters
        """
        ret = reference.find(u'spell', [u'cats grace'])
        self.assertNoRxDiff(
                [re.escape("EXACT: \037Cat's Grace\037   Transmutation || Level: Bard 2, Druid 2, Ranger 2, Sorcerer/Wizard 2 || Casting Time: 1 standard action || VSM || Range: Touch || Target: Creature touched || Duration: 1 min./level || Save: Will negates (harmless) || \002Subject gains +4 to Dex for 1 min./level.\002 || http://www.d20srd.org/srd/spells/catsGrace.htm"),
                    ],
                ret,
                'expected (regex)', 'actual')

    def test_findAmbiguousExact(self):
        """
        I can search for spells which have names that are part of
        some other spell, even when there are multiple words
        """
        ret = reference.find(u'spell', [u'cure light wounds'])
        self.assertNoRxDiff(
                [re.escape('EXACT: \037Cure Light Wounds\037   Conjuration (Healing) || Level: Bard 1, Cleric 1, Druid 1, Healing 1, Paladin 1, Ranger 2 || Casting Time: 1 standard action || VS || Range: Touch || Target: Creature touched || Duration: Instantaneous || Save: Will half (harmless); see text || \002Cures 1d8 damage +1/level (max +5).\002 || http://www.d20srd.org/srd/spells/cureLightWounds.htm'),
                    ],
                ret,
                'expected (regex)', 'actual')

    def test_monster(self):
        ret = reference.find(u'monster', [u'mohrg'])
        self.assertNoRxDiff(
                [re.escape('EXACT: \037Mohrg\037   Chaotic Evil Medium Undead || Init \002+9\002 || Darkvision 60 ft. Listen +11 Spot +15 || AC \00223 (+4 Dex, +9 natural), touch 14, flat-footed 14\002 || 14d12 HD || Fort +4 Ref +10 Will +9 || 30 ft. (6 squares) \002|| MELEE Slam +12 (1d6+7) melee, and tongue +12 (paralysis) melee \002|| Atk Options Improved grab, paralyzing touch, create spawn || Str 21, Dex 19, Con -, Int 11, Wis 10, Cha 10 || SQ Darkvision 60 ft., undead traits || http://www.d20srd.org/srd/monsters/mohrg.htm'),
                    ],
                ret,
                'expected (regex)', 'actual')
