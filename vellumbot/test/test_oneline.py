"""
Quickly moving tests from goonmill to vellumbot to keep them together..
"""
from twisted.trial import unittest

from playtools import fact, publish

from vellumbot.server import oneline

SRD = fact.systems['D20 SRD']
MONSTERS = SRD.facts['monster']

class KludgeTest(unittest.TestCase):
    def test_oneLine(self):
        """
        Make sure one-line descriptions are correctly formatted
        """
        anaxim = MONSTERS.lookup(1)
        expected = u'<<Anaxim>> Lawful Neutral Medium Construct || Init +7 (Dex) || Darkvision 60 ft., Low-Light Vision Listen +0 Spot +0 || AC 37 (+7 Dex, +20 natural), touch 17, flat-footed 30 || 38d10 HD || Fort +12 Ref +19 Will +17 || 60 ft., fly 200 ft. (perfect) || MELEE 2 spinning blades +43 (2d6+12/19-20 (plus 1d6 on critical)) melee, and 2 slams +35 (2d6+6) melee, and shocking touch +35 (2d6+6) melee RANGED electricity ray +35 (10d6 electricity) ranged, and 6 spikes +30 (2d6+12) ranged (120 ft. range increment) || Atk Options Rend 4d6+18, sonic blast, spell-like abilities, summon iron golem || Spell-Like: <div level="8" topic="Spell-Like Abilities"><p><b>Spell-Like Abilities:</b> At will-<i>greater dispel magic</i>,  <i>displacement</i> (DC 18),  <i>greater invisibility</i> (DC 19),  <i>ethereal jaunt</i>. Caster level 22nd. The save DCs are Charisma-based.</p>\n</div> || Str 35, Dex 25, Con -, Int 10, Wis 20, Cha 20 || SQ Abomination traits, magic immunity, construct traits, fast healing 15, spell resistance 34, damage reduction 10/chaotic and epic and adamantine || http://www.d20srd.org/srd/epic/monsters/anaxim.htm'
        self.assertEqual(publish.publish(anaxim, 'oneLine'), expected)
        mohrg = MONSTERS.lookup(501)
        expected = u'<<Mohrg>> Chaotic Evil Medium Undead || Init +9 || Darkvision 60 ft. Listen +11 Spot +15 || AC 23 (+4 Dex, +9 natural), touch 14, flat-footed 14 || 14d12 HD || Fort +4 Ref +10 Will +9 || 30 ft. (6 squares) || MELEE Slam +12 (1d6+7) melee, and tongue +12 (paralysis) melee || Atk Options Improved grab, paralyzing touch, create spawn || Str 21, Dex 19, Con -, Int 11, Wis 10, Cha 10 || SQ Darkvision 60 ft., undead traits || http://www.d20srd.org/srd/monsters/mohrg.htm'
        self.assertEqual(publish.publish(mohrg, 'oneLine'), expected)

        expected = ur'\037Mohrg\017 Chaotic Evil Medium Undead || Init \002+9\017 || Darkvision 60 ft. Listen +11 Spot +15 || AC \00223 (+4 Dex, +9 natural), touch 14, flat-footed 14\017 || 14d12 HD || Fort +4 Ref +10 Will +9 || 30 ft. (6 squares) \002|| MELEE Slam +12 (1d6+7) melee, and tongue +12 (paralysis) melee \017|| Atk Options Improved grab, paralyzing touch, create spawn || Str 21, Dex 19, Con -, Int 11, Wis 10, Cha 10 || SQ Darkvision 60 ft., undead traits || http://www.d20srd.org/srd/monsters/mohrg.htm'
        self.assertEqual(publish.publish(mohrg, 'richIRC'), expected)
