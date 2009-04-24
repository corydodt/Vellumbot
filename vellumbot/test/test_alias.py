import unittest
from ..server import alias
from playtools import dice, diceparser

class AliasTestCase(unittest.TestCase):
    def test_formatAlias(self):
        """
        Used aliases can be displayed as a human-readable result
        """
        a = 'foobie bletch'
        v1 = ['foo', 'bar']
        v2 = []
        v3 = ['foo']
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

    def test_getResult(self):
        """
        Dice results can be rolled and their values are accurate
        """
        aliases = {}
        # junk
        self.assertTrue(alias.getResult('anything', 'foo', aliases) is None)
        # define an alias
        _exp = diceparser.parseDice('1d1')
        self.assertEqual(alias.getResult('anything', 'foo', aliases, _exp)[0].sum(), 1)
        # junk after defining real aliases
        self.assertTrue(alias.getResult('anything', 'bar', aliases) is None)
        _exp = diceparser.parseDice('500')
        # define and recall an alias
        self.assertEqual(alias.getResult('anything', 'bar', aliases, _exp)[0].sum(), 500)
        self.assertEqual(alias.getResult('anything', 'bar', aliases)[0].sum(), 500)
        # recall the first alias
        self.assertEqual(alias.getResult('anything', 'foo', aliases)[0].sum(), 1)
        _exp = diceparser.parseDice('5')
        # redefine and recall an alias
        self.assertEqual(alias.getResult('anything', 'foo', aliases, _exp)[0].sum(), 5)
        self.assertEqual(alias.getResult('anything', 'foo', aliases)[0].sum(), 5)
        # temp modifier
        self.assertEqual(alias.getResult('anything', 'foo', aliases, None, 0)[0].sum(), 5)

    def test_shortFormatAliases(self):
        """
        Aliases can be formatted into human-readable strings that are short
        """
        aliases = {'foobar': {('buncha', 'crunch'): '2d20+20',
                              ('yums',): '1234'
                              },
                   'empty': {},
                   }
        self.assertEqual(alias.shortFormatAliases('foobar', aliases), (
                'buncha crunch=2d20+20, yums=1234'))
        self.assertEqual(alias.shortFormatAliases('empty', aliases), '(none)')
        self.assertEqual(alias.shortFormatAliases('NOBODY', aliases), '(none)')

    def test_resolve(self):
        """
        A stringy version of a result or None is returned by resolve
        """
        aliases = {}
        _exp = diceparser.parseDice('1d1')
        actor = 'GeeEm'
        verbs = tuple('smack down'.split())

        formatted = alias.resolve(actor, verbs, parsed_dice=_exp, 
                temp_modifier=2, aliases=aliases)
        self.assertEqual(formatted, 'GeeEm, you rolled: smack down d1 +2 = [1+2 = 3]')

        _exp = None
        verbs = tuple('this no Alias iS'.split())
        formatted = alias.resolve(actor, verbs, parsed_dice = _exp,
                temp_modifier=None, aliases=aliases)
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
            res.append((user, rolled[0].sum()))

        actor = 'testing alias hooks'
        verbs = 'smack down'

        # test that nothing happens when it is not registered..
        _dontcare = alias.resolve(actor, verbs, parsed_dice=_exp, 
                temp_modifier=2, aliases=aliases)
        self.assertEqual(res, [], 
                "should not have called smackDownHook here but did")

        # now register and do it again
        alias.registerAliasHook('smack down', smackDownHook)
        _dontcare = alias.resolve(actor, verbs, parsed_dice=_exp, 
                temp_modifier=2, aliases=aliases)
        self.assertEqual(res, [('testing alias hooks', 3)], 
                "should have called smackDownHook here but did not")

