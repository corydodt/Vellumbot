import unittest

class ResponseTest:
    """Notation for testing a response to a command."""
    def __init__(self, factory, user, channel, sent, *recipients):
        self.user = user
        self.factory = factory
        self.channel = channel
        self.sent = sent

        if len(recipients) == 0:
            self.recipients = None
        else:
            self.recipients = list(recipients)

        self.last_pos = 0

    def check(self):
        pipe = self.factory.pipe
        pipe.seek(self.factory.pipe_pos)
        actual = pipe.read().strip()
        self.factory.pipe_pos = pipe.tell()
        if self.recipients is None:
            if actual == '':
                pass
            else:
                print
                print "(Expected: '')"
                print actual
                return
        else:
            for _line in actual.splitlines():
                for target, expected in self.recipients:
                    pattern = 'PRIVMSG %s :%s' % (re.escape(target), 
                                                  expected)
                    # remove a recipient each time a line is found
                    # matching a line that was expected
                    if re.match(pattern, _line):
                        self.satisfy(target, expected)
                # pass when there are no recipients left to satisfy
                if len(self.recipients) == 0:
                    break
            else:
                print
                for target, expected in self.recipients:
                    print ' '*10 + ' '*len(target) + expected
                print actual
                return
        return 1

    def satisfy(self, target, expected):
        self.recipients.remove((target, expected))


class ResponseTestFactory:
    def __init__(self, pipe):
        self.pipe = pipe
        self.pipe_pos = 0

    def next(self, user, channel, target, *recipients):
        return ResponseTest(self,
                            user,
                            channel, 
                            target, 
                            *recipients)


class IRCTestCase(unittest.TestCase):
    def test_everything(self):
        passed = 0
        def succeed():
            global passed
            passed = passed + 1
            sys.stdout.write('.')

        from twisted.words.test.test_irc import StringIOWithoutClosing
        pipe = StringIOWithoutClosing()
        factory = ResponseTestFactory(pipe)
        GeeEm = (lambda channel, target, *recipients: 
                    factory.next('GeeEm', channel, target, *recipients))
        Player = (lambda channel, target, *recipients: 
                    factory.next('Player', channel, target, *recipients))

        testcommands = [
        GeeEm('VellumTalk', 'hello',),
        GeeEm('VellumTalk', 'OtherGuy: hello',),
        GeeEm('VellumTalk', 'VellumTalk: hello', ('GeeEm', r'Hello GeeEm\.')),
        GeeEm('VellumTalk', 'Vellumtalk: hello there', ('GeeEm', r'Hello GeeEm\.')),
        GeeEm('VellumTalk', '.hello', ('GeeEm', r'Hello GeeEm\.')),
        GeeEm('#testing', 'hello',),
        GeeEm('#testing', 'VellumTalk: hello', ('#testing', r'Hello GeeEm\.')),
        GeeEm('#testing', '.hello', ('#testing', r'Hello GeeEm\.')),
        GeeEm('VellumTalk', '.inits', ('GeeEm', r'Initiative list: \(none\)')),
        GeeEm('VellumTalk', '.combat', ('GeeEm', r'\*\* Beginning combat \*\*')),
        GeeEm('#testing', '[init 20]', 
              ('#testing', r'GeeEm, you rolled: init 20 = \[20\]')),
        GeeEm('VellumTalk', '.n', ('GeeEm', r'\+\+ New round \+\+')),
        GeeEm('VellumTalk', '.n', 
              ('GeeEm', r'GeeEm \(init 20\) is ready to act \. \. \.')),
        GeeEm('VellumTalk', '.p', ('GeeEm', r'\+\+ New round \+\+')),
        GeeEm('VellumTalk', '.p', 
              ('GeeEm', r'GeeEm \(init 20\) is ready to act \. \. \.')),
        GeeEm('VellumTalk', '.inits', 
              ('GeeEm', r'Initiative list: GeeEm/20, NEW ROUND/9999')),
        # GeeEm('VellumTalk', '.help', ('GeeEm', r'\s+hello: Greet\.')), FIXME
        GeeEm('VellumTalk', '.aliases', ('GeeEm', r'Aliases for GeeEm:   init=20')),
        GeeEm('VellumTalk', '.aliases GeeEm', 
              ('GeeEm', r'Aliases for GeeEm:   init=20')),
        GeeEm('VellumTalk', '.unalias foobar', 
              ('GeeEm', r'\*\* No alias "foobar" for GeeEm')),
        GeeEm('#testing',  'hello [argh 20] [foobar 30]', 
              ('#testing', r'GeeEm, you rolled: argh 20 = \[20\]')),
        GeeEm('#testing',  '[argh +1]', 
              ('#testing', r'GeeEm, you rolled: argh \+1 = \[20\+1 = 21\]')),
        GeeEm('VellumTalk', '.unalias init', 
              ('GeeEm', r'GeeEm, removed your alias for init')),
        GeeEm('VellumTalk', '.aliases', 
              ('GeeEm', r'Aliases for GeeEm:   argh=20, foobar=30')),
        ]

        testhijack = [
        GeeEm('VellumTalk', '*grimlock1 does a [smackdown 1000]', 
              ('GeeEm', 'grimlock1, you rolled: smackdown 1000 = \[1000\]')),
        GeeEm('#testing', '*grimlock1 does a [bitchslap 1000]', 
              ('#testing', 'grimlock1, you rolled: bitchslap 1000 = \[1000\]')),
        GeeEm('VellumTalk', '*grimlock1 does a [smackdown]', 
              ('GeeEm', 'grimlock1, you rolled: smackdown = \[1000\]')),
        GeeEm('VellumTalk', 'I do a [smackdown]'),
        GeeEm('VellumTalk', '.aliases grimlock1', 
              ('GeeEm', 'Aliases for grimlock1:   bitchslap=1000, smackdown=1000')),
        GeeEm('VellumTalk', '.unalias grimlock1 smackdown', 
              ('GeeEm', 'grimlock1, removed your alias for smackdown')),
        GeeEm('VellumTalk', '.aliases grimlock1', 
              ('GeeEm', 'Aliases for grimlock1:   bitchslap=1000')),
        ]

        testobserved = [
        GeeEm('VellumTalk', '.gm', 
              ('GeeEm', r'GeeEm is now a GM and will observe private messages for session #testing')),
        Player('VellumTalk', '[stabtastic 20]', 
           ('GeeEm', r'Player, you rolled: stabtastic 20 = \[20\] \(<Player>  \[stabtastic 20\]\)'),
           ('Player', r'Player, you rolled: stabtastic 20 = \[20\] \(observed\)')
           )
        ]

        testobserverchange = [
        GeeEm("VellumTalk", '[stabtastic 20]',
                ('GeeEm', r'GeeEm, you rolled: stabtastic 20 = \[20\]$'),
              )
        ]

        testunobserved = [
        Player('VellumTalk', '[stabtastic 20]', 
           ('Player', r'Player, you rolled: stabtastic 20 = \[20\]$')
           )
        ]
        # TODO - move d20-specific tests, e.g. init and other alias hooks?

        def test():
            # save off and clear alias.aliases, since it gets persisted # FIXME
            orig_aliases = alias.aliases
            alias.aliases = {}
            try:
                transport = protocol.FileWrapper(pipe)
                vt = VellumTalk()
                vt.performLogin = 0
                vt.joined("#testing")
                vt.defaultSession = d20session.D20Session('#testing')
                vt.makeConnection(transport)

                testOneSet(testcommands, vt)
                testOneSet(testhijack, vt)
                testOneSet(testobserved, vt)

                vt.userRenamed('Player', 'Superman')
                testOneSet(testobserverchange, vt)
                vt.userLeft('GeeEm', '#testing')
                testOneSet(testunobserved, vt)
            finally:
                # restore original aliases when done, so save works
                alias.aliases = orig_aliases
                global passed
                print passed
                passed = 0

        def testOneSet(test_list, vt):
            for r in test_list:
                vt.privmsg(r.user, r.channel, r.sent)
                if r.check():
                    succeed()
