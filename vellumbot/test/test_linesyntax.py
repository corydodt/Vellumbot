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

        pvp = lambda s: str(linesyntax.parseVerbPhrase(s.encode('utf-8')))

        eq(pvp(u"[1d20+1]"),                         "d20+1")
        eq(pvp(u"[star]"),                           'star')
        eq(pvp(u"[rOck   star]"),                    'rock star')
        eq(pvp(u"[woo 1d20+1]"),                     'woo d20+1')
        eq(pvp(u"[arr matey 1d20+1x7sort]"),         'arr matey d20+1x7sort')
        eq(pvp(u"[woo +2]"),                         'woo +2')
        # eq(pvp(u"[woo ث +2]"),                       'woo ث +2') no non-ascii support yet
        eq(pvp(u"[woo -2]"),                         'woo -2')
        eraise(u"[]",                                ParserSyntaxError)
        eraise(u"[i am a star",                      ParserSyntaxError)
        eraise(u"[1d20+1 1d20+1]",                   ParserSyntaxError)
        #

    def test_commands(self):
        _test_commands = [
        (u".hello",                                  [(None, 'hello', None)]),
        (u".foo bar",                                [(None, 'foo', 'bar')]),
        # (u".ثfoo bar",                               [(None, 'ثfoo', 'bar')]), # no non-ascii support
        (u". foo",                                   [(None, 'foo', None)]),
        (u"..foo",                                   ParserSyntaxError),
        (u"VellumBot:foo",                           [('vellumbot', 'foo', None)]),
        (u"velluMBot,foo",                           [('vellumbot', 'foo', None)]),
        (u"VellumBot foo",                           RuntimeError),
        (u"VellumBot: foo",                          [('vellumbot', 'foo', None)]),
        (u"velluMBot, foo",                          [('vellumbot', 'foo', None)]),
        (u"tesTBotfoo",                              RuntimeError),
        ]

        for tc, expect in _test_commands:
            if expect in (ParserSyntaxError, RuntimeError):
                parse = lambda s: linesyntax.parseCommand(s)
                self.assertRaises(expect, parse, tc)
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

        sen = lambda s: linesyntax.parseSentence(s.encode('utf-8'))

        eqsent(sen(u'.gm'),                     {'command': 'gm',
        'commandArgs': []})
        eqsent(sen(u'.charname bob bob'),       {'command': 'charname', 
                                                'commandArgs': ['bob', 'bob']})
        r = sen(u"TestBot, n")
        self.assertEqual(r.botName,             'testbot')
        eqsent(sen(u"TestBot, n"),              {'command': 'n',
                                                'commandArgs': []})
        eqsent(sen(u"testbot, n"),              {'command': 'n',
                                                'commandArgs': []})
        errsent(u"testbot n",                   RuntimeError)
        eqsent(sen(u".aliases shara"),          {'command': 'aliases',
                                                'commandArgs': ['shara']})
        eqsent(sen(u".foobly 'do obly' doo"),   '.foobly "do obly" doo')
        
        
        errsent(u"lalala",                      RuntimeError)  
        errsent(u"*woop1",                      RuntimeError) # missing verb
        errsent(u"*jack and *jill [1d20+1]",    RuntimeError) # extra actors
        eqsent(sen(u"[attack attack 1d2+10]"),  "[attack attack d2+10].")
        eqsent(sen(u"[foo] *woop2"),            "*woop2 does [foo].")
        # eqsent(sen(u"[foo] is done by *ث"),     "*ث does [foo].") # no non-ascii support
        # eqsent(sen(u"[ثfoo] is done by *woop2"),     "*woops does [ثfoo].") # no non-ascii support
        eqsent(sen(u"The [machinegun] being fired at @Shara by the *ninja goes rat-a-tat."),
                                                "*ninja does [machinegun] to @Shara.")
        eqsent(sen(u"*grimlock1 [attack 1d2+10]s the paladin. (@shara)"),
                                                "*grimlock1 does [attack d2+10] to @shara.")
        eqsent(sen(u"I [attack 1d6+1] @grimlock1"),
                                                "[attack d6+1] to @grimlock1.")
        eqsent(sen(u"I [attack -1] @grimlock1"), 
                                                "[attack -1] to @grimlock1.")
        eqsent(sen(u"I [attack +1] @grimlock1"), 
                                                "[attack +1] to @grimlock1.")
        eqsent(sen(u"I [attack 1d6+1x2sort] @grimlock1"), 
                                                "[attack d6+1x2sort] to @grimlock1.")
        eqsent(sen(u"I [cast] a [fireball] @grimlock1 and @grimlock2"),
                                                "[cast][fireball] to @grimlock1 and @grimlock2.")
        eqsent(sen(u"I [cast] a [fireball] @grimlock1 and@grimlock2"),
                                                "[cast][fireball] to @grimlock1 and @grimlock2.")
        #

