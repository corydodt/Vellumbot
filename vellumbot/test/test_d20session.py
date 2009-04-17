"""
D20Session tests
"""
import operator

from twisted.trial import unittest
from vellumbot.server import d20session

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
