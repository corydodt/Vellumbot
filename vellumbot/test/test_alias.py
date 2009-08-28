import unittest
from ..server import alias
from .. import user
from playtools import dice
from playtools.parser import diceparser

class AliasTestCase(unittest.TestCase):
    def setUp(self):
        self.store = user.userDatabase('sqlite:')

    def test_formatAlias(self):
        """
        Used aliases can be displayed as a human-readable result
        """
        a = u'foobie bletch'
        v1 = (u'foo', u'bar')
        v2 = ()
        v3 = (u'foo',)
        parsed_dice = diceparser.parseDice('1d20x3')
        parsed_dice2 = diceparser.parseDice('1d20x3sort')
        parsed_dice3 = ''
        parsed_dice4 = diceparser.parseDice('3d6+2')

        R = lambda n: dice.DiceResult([n], 0)
        results = [R(10), R(15), R(5)]
        results2 = [dice.DiceResult([3,4,5], 2)]
        results3 = [dice.DiceResult([3,4,5], 2, 2)]

        fmtd = alias.formatAlias(a, v1, results[:], parsed_dice)
        self.assertEqual(fmtd, 'foobie bletch, you rolled: foo bar d20x3 = [10, 15, 5]')
        fmtd = alias.formatAlias(a, v2, results[:], parsed_dice)
        self.assertEqual(fmtd, 'foobie bletch, you rolled: d20x3 = [10, 15, 5]')
        fmtd = alias.formatAlias(a, v3, results[:], parsed_dice) 
        self.assertEqual(fmtd, 'foobie bletch, you rolled: foo d20x3 = [10, 15, 5]')
        fmtd = alias.formatAlias(a, v3, results[:], parsed_dice3) 
        self.assertEqual(fmtd, 'foobie bletch, you rolled: foo = [10, 15, 5]')
        fmtd = alias.formatAlias(a, v2, results[:], parsed_dice2) 
        self.assertEqual(fmtd, 'foobie bletch, you rolled: d20x3sort = [5, 10, 15] (sorted)')
        fmtd = alias.formatAlias(a, v2, results2[:], parsed_dice4) 
        self.assertEqual(fmtd, 'foobie bletch, you rolled: 3d6+2 = [3+4+5+2 = 14]')
        fmtd = alias.formatAlias(a, v2, results3[:], parsed_dice4, 2) 
        self.assertEqual(fmtd, 'foobie bletch, you rolled: 3d6+2 +2 = [3+4+5+2+2 = 16]')

    def test_shortFormatAliases(self):
        """
        Aliases can be formatted into human-readable strings that are short
        """
        add = lambda *a: [self.store.add(x) for x in a]
        foobar = user.User()
        buncha = user.Alias()
        yums = user.Alias()
        add(foobar, buncha, yums)
        foobar.aliases = [user.Alias(), user.Alias()]
        foobar.aliases[0].words = u'buncha crunch'
        foobar.aliases[0].expression = u'2d20+20'
        foobar.aliases[1].words = u'yums'
        foobar.aliases[1].expression = u'1234'
        self.assertEqual(alias.shortFormatAliases(foobar),
                u'buncha crunch=2d20+20, yums=1234')

        empty = user.User()
        add(empty)
        self.assertEqual(alias.shortFormatAliases(empty), '(none)')

    def test_getResult(self):
        """
        Dice results can be rolled and their values are accurate
        """
        ne1 = user.User()
        ne1.name = u'ne1'
        self.store.add(ne1)
        self.store.commit()
        # junk
        self.assertTrue(alias.getResult(ne1, (u'foo',), ) is None)
        # define an alias
        _exp = diceparser.parseDice(u'1d1')
        self.assertEqual(alias.getResult(ne1, (u'sha', u'zam'), _exp)[0].sum(), 1)
        # junk after defining real aliases
        self.assertTrue(alias.getResult(ne1, (u'bar',), ) is None)
        _exp = diceparser.parseDice('500')
        # define and recall an alias
        self.assertEqual(alias.getResult(ne1, (u'bar',), _exp)[0].sum(), 500)
        self.assertEqual(alias.getResult(ne1, (u'bar',), )[0].sum(), 500)
        # recall the first alias
        self.assertEqual(alias.getResult(ne1, (u'sha', u'zam'), )[0].sum(), 1)
        _exp = diceparser.parseDice('5')
        # redefine and recall an alias
        self.assertEqual(alias.getResult(ne1, (u'sha', u'zam'), _exp)[0].sum(), 5)
        self.assertEqual(alias.getResult(ne1, (u'sha', u'zam'), )[0].sum(), 5)
        # temp modifier
        self.assertEqual(alias.getResult(ne1, (u'sha', u'zam'), None, 0)[0].sum(), 5)

    def test_resolve(self):
        """
        A stringy version of a result or None is returned by resolve
        """
        ne1 = user.User()
        ne1.name = u'GeeEm'
        ne1.network = u'FIXME TODO'
        self.store.add(ne1)
        self.store.commit()

        _exp = diceparser.parseDice('1d1')
        verbs = (u'smack', u'down')

        formatted = alias.resolve(ne1, verbs, parsed_dice=_exp, 
                temp_modifier=2, )
        self.assertEqual(formatted, 'GeeEm, you rolled: smack down d1 +2 = [1+2 = 3]')

        _exp = None
        verbs = tuple('this no Alias iS'.split())
        formatted = alias.resolve(ne1, verbs, parsed_dice = _exp,
                temp_modifier=None, )
        self.assertEqual(formatted, None)

    def test_aliasHooks(self):
        """
        We can associate a callable with an alias, and that callable will get
        called when we roll the dice
        """
        aliases = {}
        res = []
        _exp = diceparser.parseDice('1d1')

        def smackDownHook(user, rolled):
            """
            We take a string for the user who invoked the alias and an object
            which is the structured result of the roll
            """
            res.append((user.name, rolled[0].sum()))

        ne1 = user.User()
        ne1.name = u'testing alias hooks'
        ne1.network = u'FIXME TODO'
        self.store.add(ne1)
        self.store.commit()
        verbs = (u'smack', u'down')

        # test that nothing happens when it is not registered..
        _dontcare = alias.resolve(ne1, verbs, parsed_dice=_exp, 
                temp_modifier=2)
        self.assertEqual(res, [], 
                "should not have called smackDownHook here but did")

        # now register and do it again
        alias.registerAliasHook((u'smack', u'down'), smackDownHook)
        _dontcare = alias.resolve(ne1, verbs, parsed_dice=_exp, 
                temp_modifier=2, )
        self.assertEqual(res, [(u'testing alias hooks', 3)], 
                "should have called smackDownHook here but did not")

