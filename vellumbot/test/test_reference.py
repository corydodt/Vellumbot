import unittest

from . import util

class ReferenceTestCase(unittest.TestCase, util.DiffTestCaseMixin):
    """
    Test lookups and references
    """

    def test_lookup(self):
        """
        Check that the searching of spell database works.
        """
        from ..server import reference
        ret = reference.lookup(u'spell', [u'fireball'])
        # test exact match one word
        self.assertNoRxDiff(
                r'<<Fireball>> Evocation || Level: Sorcerer/Wizard 3 || Casting Time: 1 standard action || VSM || Range: Long \(400 ft\. + 40 ft\./level\) || Area: 20-ft\. -radius spread || Duration: Instantaneous || Save: Reflex half || 1d6 damage per level, 20-ft\. radius\. || http://www\.d20srd\.org/srd/spells/fireball\.htm',
                ret[0],
                'expected (regex)', 'actual')
        # test exact match multiple words
        ret = reference.lookup(u'spell', [u'cure serious wounds mass'])
        self.assertNoRxDiff(
                r'<<Cure Serious Wounds, Mass>> Conjuration \(Healing\) || Level: Cleric 7, Druid 8 || Casting Time: 1 standard action || VS || Range: Close \(25 ft\. + 5 ft\./2 levels\) || Target: One creature/level, no two of which can be more than 30 ft\. apart || Duration: Instantaneous || Save: Will half \(harmless\) or Will half; see text || Cures 3d8 damage +1/level for many creatures\. || http://www\.d20srd\.org/srd/spells/cureSeriousWoundsMass\.htm',
                ret[0],
                'expected (regex)', 'actual')
        # test non-exact match
        ret = reference.lookup(u'spell', [u'cure'])
        self.assertEqual(len(ret), 5)
        self.assertNoRxDiff(
                ur'"cure light wounds mass": \*\*Cure\*\* Light Wounds, Mass Conjuration.*, mass.*\.\.\.', 
                ret[0],
                'expected (regex)', 'actual')
