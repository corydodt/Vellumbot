"""
D20Session tests
"""
import operator
import re

from twisted.trial import unittest

import vellumbot.server.session
from ..server import d20session
from . import util

class TestD20Session(util.BotTestCase):
    def test_reference(self):
        """
        I respond to people who look things up
        """
        vellumbot.server.session.TESTING = True
        vellumbot.server.irc.TESTING = True
        geeEm = lambda *a, **kw: self.anyone('GeeEm', *a, **kw)
        player = lambda *a, **kw: self.anyone('Player', *a, **kw)
        self.addUser(u'GeeEm')

        self.vt.userJoined("Player", "#testing")

        geeEm('#testing', '.gm', 
              ('#testing', r'GeeEm is now a GM and will observe private messages for session #testing'))

        lines1 = '''"cure light wounds mass": **Cure** Light Wounds, Mass Conjuration ...  positive energy to **cure** 1d8 points of damag ... reature. Like other **cure** spells, mass **cure** l ... 
"cure minor wounds": **Cure** Minor Wounds Conjuration (Heal ... pell functions like **cure** light wounds , exce ... pt that it **cure**s only 1 point of da ... 
"cure critical wounds": **Cure** Critical Wounds Conjuration (H ... pell functions like **cure** light wounds , exce ... pt that it **cure**s 4d8 points of dama ... 
"cure moderate wounds": **Cure** Moderate Wounds Conjuration (H ... pell functions like **cure** light wounds , exce ... pt that it **cure**s 2d8 points of dama ... 
"cure serious wounds": **Cure** Serious Wounds Conjuration (He ... pell functions like **cure** light wounds , exce ... pt that it **cure**s 3d8 points of dama ... '''.split('\n')

        expectations1 = []
        for line in lines1:
            expectations1.append(('Player', '%s \(observed\)' % (re.escape(line),)))
            expectations1.append(('GeeEm', '<Player>  \.lookup spell cure  ===>  %s' % (re.escape(line),)))
        expectations1.append(('Player', 
            r'Replied to Player with top 5 matches for SPELL "cure" \(observed\)'))
        expectations1.append(('GeeEm', 
            r'<Player>  \.lookup spell cure  ===>  Replied to Player with top 5 matches for SPELL "cure"'))

        player('VellumTalk', '.lookup spell cure', *expectations1)

        expectations2 = []
        for line in lines1:
            expectations2.append(('Player', '%s' % (re.escape(line),)))
        expectations2.append(('#testing', 
            r'Replied to Player with top 5 matches for SPELL "cure"'))

        player('#testing', '.lookup spell cure', *expectations2)

        # this spell goes over the 420 char limit.  rig it to make this test
        # simpler
        vellumbot.server.irc.MAX_LINE = 600
        try:
            player('#testing', '.lookup spell cure serious wounds mass', (
                '#testing', 
                'Player: SPELL EXACT: \037Cure Serious Wounds, Mass\017   .*',
                )
            )
        
            player('#testing', '.lookup spell wenis', (
                '#testing', 
                r'Player: No SPELL contains "wenis"\.  Try searching with a wildcard e\.g\. \.lookup spell wenis\*'),
            )
            player('#testing', '.lookup spell wenis*', (
                '#testing', 
                r'Player: No SPELL contains "wenis\*"\.'),
            )

            lines2 = '''"heal mass": Heal, Mass Conjuration \(Healing\) Le \.\.\.
"heal": Heal Conjuration \(Healing\) Level: C \.\.\.
"heal mount": Heal Mount Conjuration \(Healing\) Le \.\.\.
"seed heal": Seed: Heal Conjuration \(Healing\) Sp \.\.\.
"cure critical wounds": Cure Critical Wounds Conjuration \(H \.\.\.'''.split('\n')
            expectations3 = []
            for line in lines2:
                expectations3.append(('Player', line))
            expectations3.append(('#testing', 'Replied to Player with top 5 matches for SPELL "heal\*"'))
            player('#testing', '.lookup spell heal*', *expectations3)

            player('#testing', '.lookup monster mohrg', (
                '#testing', 
                r'Player: MONSTER EXACT: \037Mohrg\017   Chaotic Evil .*mohrg.htm'
                )
            )
        finally:
            vellumbot.server.irc.MAX_LINE = 420 

    def test_lookupFeat(self):
        """
        I know how to look up feats
        """
        geeEm = lambda *a, **kw: self.anyone('GeeEm', *a, **kw)
        self.addUser(u'GeeEm')
        benefit = "Benefit:  In melee, every time you miss because of concealment, you can reroll .*"
        vellumbot.server.irc.MAX_LINE = 800
        geeEm('#testing', '.lookup feat blindfight', (
            '#testing', 
            r'GeeEm: FEAT EXACT: \037Blind-Fight\017   ' + benefit,
            )
        )

    def test_lookupSkill(self):
        """
        I know how to look up skills
        """
        geeEm = lambda *a, **kw: self.anyone('GeeEm', *a, **kw)
        self.addUser(u'GeeEm')
        vellumbot.server.irc.MAX_LINE = 600
        geeEm('#testing', '.lookup skill concentration', (
            '#testing', 
            r'GeeEm: SKILL EXACT: \037Concentration\017   Key Ability: Con.*', 
            )
        )

    def test_failedReference(self):
        """
        Lookups that refer to things that I don't know how to look up give an
        error.
        """
        vellumbot.server.session.TESTING = True
        vellumbot.server.irc.TESTING = True
        self.addUser(u'Player')
        self.anyone('Player', '#testing', '.lookup flurfl cleave', 
                ('#testing', 'I don\'t know how to look those things up.'))

    def test_initiative(self):
        geeEm = lambda *a, **kw: self.anyone('GeeEm', *a, **kw)
        self.addUser(u'GeeEm')

        geeEm('VellumTalk', '.inits', ('GeeEm', r'INITIATIVES: \(none\)'))
        geeEm('#testing', '.combat', 
            ('#testing', r'\*\* Beginning combat \*\*'))
        # now: newround
        geeEm('#testing', '[4d1+2]', 
              ('#testing', r'GeeEm, you rolled: 4d1\+2 = \[1\+1\+1\+1\+2 = 6\]'))
        geeEm('#testing', '[init 20]', 
              ('#testing', r'GeeEm, you rolled: init 20 = \[20\]'))
        # now: newround GeeEm
        geeEm('#testing', '.n', 
            ('#testing', r'GOING NOW: GeeEm \(20\)!  Next: new round\.'))
        # now: GeeEm newround
        geeEm('#testing', '.n', ('#testing', r'\+\+ New round \+\+  Next: GeeEm \(20\)\.'))
        # now: newround GeeEm
        geeEm('#testing', '.p', 
            ('#testing', r'GOING NOW: GeeEm \(20\)!  Next: new round\.'))
        # now: GeeEm newround
        geeEm('#testing', '.p', ('#testing', r'\+\+ New round \+\+  Next: GeeEm \(20\)\.'))
        # now: newround GeeEm
        geeEm('#testing', '.inits', 
              ('#testing', r'INITIATIVES: new round \|\| GeeEm/20'))
        geeEm('#testing', '*Hamlet [init 20]',
              ('#testing', r'Hamlet, you rolled: init 20 = \[20\]'))
        # now: newround GeeEm Hamlet
        geeEm('#testing', '.n', ('#testing', r'GOING NOW: GeeEm \(20\)!  Next: Hamlet \(20\)\.'))
        # now: GeeEm Hamlet newround
        geeEm('#testing', '.inits', 
              ('#testing', r'INITIATIVES: GeeEm/20 \|\| Hamlet/20 \|\| new round'))
        geeEm('#testing', '.n',
            ('#testing', r'GOING NOW: Hamlet \(20\)!  Next: new round\.'))
        # now: Hamlet newround GeeEm
        geeEm('#testing', '*Ophelia [init 18]',
              ('#testing', r'Ophelia, you rolled: init 18 = \[18\]'))
        # now: Hamlet Ophelia newround GeeEm
        geeEm('#testing', '*Yorick [init 2]',
              ('#testing', r'Yorick, you rolled: init 2 = \[2\]'))
        # now: Hamlet Ophelia Yorick newround GeeEm
        geeEm('#testing', '.inits', 
              ('#testing', r'INITIATIVES: Hamlet/20 \|\| Ophelia/18 \|\| Yorick/2 \|\| new round \|\| GeeEm/20'))

        # a new initiative for a player should replace the old one
        geeEm('#testing', '*Ophelia [init 1]',
              ('#testing', r'Ophelia, you rolled: init 1 = \[1\]'))
        geeEm('#testing', '.inits', 
              ('#testing', r'INITIATIVES: Hamlet/20 \|\| Yorick/2 \|\| Ophelia/1 \|\| new round \|\| GeeEm/20'))


class TestSortedRing(unittest.TestCase):
    def test_addSorted(self):
        """
        Items stay sorted when added
        """
        ring = d20session.SortedRing()
        self.assertEqual(len(ring), 0)
        ring.addSorted(4)
        self.assertEqual(len(ring), 1)
        ring.addSorted(1)
        self.assertEqual(len(ring), 2)
        self.assertEqual(ring[0], 1)
        self.assertEqual(ring[1], 4)

    def test_contains(self):
        """
        We can answer "x in ring"
        """
        alice = 'alice'
        bob = 'bob'
        carl = 'carl'
        ring = d20session.SortedRing([alice, bob])
        self.assertTrue(alice in ring)
        self.assertFalse(carl in ring)

    def test_identicalAddSort(self):
        """
        When two items that have the same sort order are in the list, the
        second one that gets added follows the first one.
        """
        A = ['a'] # these are lists because strings get interned, so test identical
        A2 = ['a']
        B = ['b']
        B2 = ['b']
        self.assertEqual(B, B2)
        ring = d20session.SortedRing([A, B]) # now:    A B
        self.assertIdentical(ring.next(), B)
        ring.addSorted(B2) # now:                      A B B2
        self.assertIdentical(ring.next(), B)
        ring.rotate(1) # now:                          B B2 A
        self.assertIdentical(ring.next(), B2)
        ring.addSorted(A2) # now:                      B B2 A A2
        ring.rotate(-1) # now:                         A2 B B2 A
        self.assertIdentical(ring.current(), A2)
        self.assertIdentical(ring.prev(), A)

    ''' # unfortunately we can't do this - bisect doesn't support key or cmp
    def test_sortKey(self):
        """
        We can change how sort order is determined
        """
        ALICE = ("Alice", 2) 
        BOB = ("Bob", 4)
        CARL = ("Carl", 1)
        # default sorting
        ring1 = d20session.SortedRing([CARL, ALICE, BOB])
        self.assertEqual(ring1[:], [ALICE, BOB, CARL])
        # customized sorting: sort by item[1]
        ring1 = d20session.SortedRing([CARL, ALICE, BOB], key=operator.itemgetter(1))
        self.assertEqual(ring1[:], [CARL, ALICE, BOB])

    '''

    def test_del(self):
        """
        When removing items the sort stays sorted.
        Delete operates on the ring.
        """
        ring = d20session.SortedRing(['a','b','c','d'])
        self.assertEqual(ring.current(), 'a')
        self.assertEqual(ring.next(), 'b')
        del ring[1] # deletes b, rotation now a c d
        self.assertEqual(ring.current(), 'a')
        self.assertEqual(ring.next(), 'c')
        del ring[0] # deletes a, rotation now c d
        self.assertEqual(ring.current(), 'c')
        self.assertEqual(ring.next(), 'd')
        del ring[0]; del ring[0] # now empty
        self.assertRaises(IndexError, ring.current)

        def _delCheck(): del ring[0]
        self.assertRaises(IndexError, _delCheck)

    def test_index(self):
        """
        The index method returns the position of an item from the sort
        """
        ring = d20session.SortedRing(['b','d','a'])
        self.assertEqual(ring.index('d'), 2)

    def test_sortRotationIndependence(self):
        """
        Operations on the sorted data return values independent from the ring
        rotation and v/v.
        """
        ring = d20session.SortedRing([1,2,4])
        self.assertEqual(ring.current(), 1)
        ring.rotate(1)
        self.assertEqual(ring.current(), 2)
        self.assertEqual(ring.index(2), 1)
        self.assertEqual(ring[:], [1,2,4])
        self.assertEqual(ring[2], 4)

        # current ring order is: 2 4 1 after the last rotate
        self.assertEqual(ring.next(), 4)
        ring.addSorted(3)
        self.assertEqual(ring.next(), 3)
        self.assertEqual(ring.current(), 2)
        self.assertEqual(ring.prev(), 1)

        ring.rotate(1)
        self.assertEqual(ring.next(), 4)
        # current rotation now: 3 4 1 2
        del ring[ring.index(4)]
        self.assertEqual(ring.current(), 3)
        self.assertEqual(ring.next(), 1)

    def test_slice(self):
        """
        Slices of the list contain the items in sort order
        """
        ring = d20session.SortedRing([4,1])
        self.assertEqual(ring[:], [1,4])

    def test_positionOperators(self):
        """
        The position operators current, next and prev indicate the position in
        the ring.
        """
        ring = d20session.SortedRing([2,4,1])
        self.assertEqual(ring.current(), 1)
        self.assertEqual(ring.next(), 2)
        self.assertEqual(ring.prev(), 4)

        ring = d20session.SortedRing([2])
        self.assertEqual(ring.current(), 2)
        self.assertEqual(ring.next(), 2)
        self.assertEqual(ring.prev(), 2)

        ring = d20session.SortedRing([2,4])
        self.assertEqual(ring.current(), 2)
        self.assertEqual(ring.next(), 4)
        self.assertEqual(ring.prev(), 4)

        ring = d20session.SortedRing()
        self.assertRaises(IndexError, ring.current)
        self.assertRaises(IndexError, ring.next)
        self.assertRaises(IndexError, ring.prev)

    def test_rotate(self):
        """
        Rotation forward and back take us to the expected place
        """
        ring = d20session.SortedRing(['a','b','c','d'])
        self.assertEqual(ring.current(), 'a')
        ring.rotate(2)
        self.assertEqual(ring.current(), 'c')
        ring.rotate(1)
        self.assertEqual(ring.current(), 'd')
        ring.rotate(-1)
        self.assertEqual(ring.current(), 'c')
        ring.rotate(4)
        self.assertEqual(ring.current(), 'c')
        ring.rotate(-4)
        self.assertEqual(ring.current(), 'c')
        ring.rotate()
        self.assertEqual(ring.current(), 'd')
        ring.rotate(73)
        self.assertEqual(ring.current(), 'a')

    def test_asRotatedList(self):
        """
        Show all items in their rotated position
        """
        ring = d20session.SortedRing(['a','b','c','d'])
        ring.rotate(2)
        self.assertEqual(ring.asRotatedList(), ['c','d','a','b'])
