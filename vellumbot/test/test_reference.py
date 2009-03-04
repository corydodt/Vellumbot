from twisted.trial import unittest
import re

from . import util
from ..server import reference

class ReferenceTestCase(unittest.TestCase, util.DiffTestCaseMixin):
    """
    Test lookups and references
    """

    def test_find(self):
        """
        Check that the searching of spell database works.
        """
        ret = reference.find(u'spell', [u'fireball'])
        # test exact match one word
        self.assertNoRxDiff(
                [re.escape(r'<<Fireball>> Evocation || Level: Sorcerer/Wizard 3 || Casting Time: 1 standard action || VSM || Range: Long (400 ft. + 40 ft./level) || Area: 20-ft. -radius spread || Duration: Instantaneous || Save: Reflex half || 1d6 damage per level, 20-ft. radius. || http://www.d20srd.org/srd/spells/fireball.htm'),
                    ],
                ret,
                'expected (regex)', 'actual')
        # test exact match multiple words
        ret = reference.find(u'spell', [u'cure serious wounds mass'])
        self.assertNoRxDiff(
                [re.escape(r'<<Cure Serious Wounds, Mass>> Conjuration (Healing) || Level: Cleric 7, Druid 8 || Casting Time: 1 standard action || VS || Range: Close (25 ft. + 5 ft./2 levels) || Target: One creature/level, no two of which can be more than 30 ft. apart || Duration: Instantaneous || Save: Will half (harmless) or Will half; see text || Cures 3d8 damage +1/level for many creatures. || http://www.d20srd.org/srd/spells/cureSeriousWoundsMass.htm'),
                    ],
                ret,
                'expected (regex)', 'actual')
        # test non-exact match
        ret = reference.find(u'spell', [u'cure'])
        self.assertEqual(len(ret), 5)
        self.assertNoRxDiff(
                [ur'"cure light wounds mass": \*\*Cure\*\* Light Wounds, Mass Conjuration.*, mass.*\.\.\.', 
                ur'.*', ur'.*', ur'.*', ur'.*'],
                ret,
                'expected (regex)', 'actual')

    def test_monster(self):
        ret = reference.find(u'monster', [u'mohrg'])
        self.assertNoRxDiff(
                [re.escape(r'<<Mohrg>> Chaotic Evil Medium Undead || Init +9 || Darkvision 60 ft., Darkvision 60 ft. Listen +11 Spot +15 || AC 23 (+4 Dex, +9 natural), touch 14, flat-footed 14 || 14d12 HD || Fort +4 Ref +10 Will +9 || 30 ft. (6 squares) || MELEE Slam +12 (1d6+7) melee, and tongue +12 (paralysis) melee || Atk Options Improved grab, paralyzing touch, create spawn || Str 21, Dex 19, Con -, Int 11, Wis 10, Cha 10 || SQ Darkvision 60 ft., undead traits || http://www.d20srd.org/srd/monsters/mohrg.htm'),
                    ],
                ret,
                'expected (regex)', 'actual')
