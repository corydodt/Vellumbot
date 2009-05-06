# vim:set fileencoding=utf-8:
import unittest

from ..server import linesyntax
from simpleparse.error import ParserSyntaxError


class LinesyntaxTestCase(unittest.TestCase):
    """
    Test that sentences, verbs and commands are parsed successfully
    """
    def test_verbPhrase(self):
        eraise = lambda s, e: self.assertRaises(e, pvp, s)
        eq = self.assertEqual
        pvp = lambda s: str(linesyntax.parseVerbPhrase(s))
        eq(str(pvp("[1d20+1]")),                    "d20+1")
        eq(pvp("[star]"),                           'star')
        eq(pvp("[rOck   star]"),                    'rock star')
        eq(pvp("[woo 1d20+1]"),                     'woo d20+1')
        eq(pvp("[arr matey 1d20+1x7sort]"),         'arr matey d20+1x7sort')
        eq(pvp("[woo +2]"),                         'woo +2')
        eq(pvp("[woo -2]"),                         'woo -2')
        eraise("[]",                                ParserSyntaxError)
        eraise("[i am a star",                      ParserSyntaxError)
        eraise("[1d20+1 1d20+1]",                   ParserSyntaxError)
        #

    def test_commands(self):
        _test_commands = [
        (".hello",                                  [(None, 'hello', None)]),
        (".foo bar",                                [(None, 'foo', 'bar')]),
        (". foo",                                   [(None, 'foo', None)]),
        ("..foo",                                   ParserSyntaxError),
        ("VellumBot:foo",                           [('vellumbot', 'foo', None)]),
        ("velluMBot,foo",                           [('vellumbot', 'foo', None)]),
        ("VellumBot foo",                           RuntimeError),
        ("VellumBot: foo",                          [('vellumbot', 'foo', None)]),
        ("velluMBot, foo",                          [('vellumbot', 'foo', None)]),
        ("tesTBotfoo",                              RuntimeError),
        ]

        for tc, expect in _test_commands:
            if expect in (ParserSyntaxError, RuntimeError):
                self.assertRaises(expect, linesyntax.parseCommand, tc)
            else:
                res = linesyntax.parseCommand(tc)
                self.assertEqual(res, expect)

    def test_sentences(self):
        def eqsent(result, assertions):
            """
            Inspect the result Sentence against the assertions
            """
            if hasattr(assertions, 'items'):
                for k,v in assertions.items():
                    self.assertEqual(getattr(result, k), v)
            elif isinstance(assertions, basestring):
                self.assertEqual(str(result), assertions)
            else:
                assert 0, "BAD TEST"

        errsent = lambda s, e: self.assertRaises(e, sen, s)

        sen = linesyntax.parseSentence
        eqsent(sen('.gm'),                     {'command': 'gm',
                                               'commandArgs': []})
        eqsent(sen('.charname bob bob'),       {'command': 'charname', 
                                               'commandArgs': ['bob','bob']})
        r = sen("TestBot, n")
        self.assertEqual(r.botName,            'testbot')  
        eqsent(sen("TestBot, n"),              {'command': 'n',
                                               'commandArgs': []})
        eqsent(sen("testbot, n"),              {'command': 'n',
                                               'commandArgs': []})
        errsent("testbot n",                   RuntimeError)
        eqsent(sen(".aliases shara"),          {'command': 'aliases',
                                               'commandArgs': ['shara']})
        eqsent(sen(".foobly 'do obly' doo"),   '.foobly "do obly" doo')
 

        errsent("lalala",                      RuntimeError)  
        errsent("*woop1",                      RuntimeError) # missing verb
        errsent("*jack and *jill [1d20+1]",    RuntimeError) # extra actors
        eqsent(sen("[attack attack 1d2+10]"),  "[attack attack d2+10].")
        eqsent(sen("[foo] *woop2"),            "*woop2 does [foo].")
        eqsent(sen("The [machinegun] being fired at @Shara by the *ninja goes rat-a-tat."),
                                               "*ninja does [machinegun] to @Shara.")
        eqsent(sen("*grimlock1 [attack 1d2+10]s the paladin. (@shara)"),
                                               "*grimlock1 does [attack d2+10] to @shara.")
        eqsent(sen("I [attack 1d6+1] @grimlock1"),
                                               "[attack d6+1] to @grimlock1.")
        eqsent(sen("I [attack -1] @grimlock1"), 
                                               "[attack -1] to @grimlock1.")
        eqsent(sen("I [attack +1] @grimlock1"), 
                                               "[attack +1] to @grimlock1.")
        eqsent(sen("I [attack 1d6+1x2sort] @grimlock1"), 
                                               "[attack d6+1x2sort] to @grimlock1.")
        eqsent(sen("I [cast] a [fireball] @grimlock1 and @grimlock2"),
                                               "[cast][fireball] to @grimlock1 and @grimlock2.")
        eqsent(sen("I [cast] a [fireball] @grimlock1 and@grimlock2"),
                                               "[cast][fireball] to @grimlock1 and @grimlock2.")
        #

