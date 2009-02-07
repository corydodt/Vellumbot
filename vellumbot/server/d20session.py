"""Session subclass specific to D20 (inits etc.)"""

from vellumbot.server import alias, session

class D20Session(session.Session):
    def __init__(self, channel):
        session.Session.__init__(self, channel)
        self.initiatives = []
        alias.registerAliasHook(('init',), self.doInitiative)

    def respondTo_n(self, user, _):
        """Next initiative"""
        next = self.initiatives.pop(0)
        self.initiatives.append(next)
        if next[1] is None:
            return '++ New round ++'
            # TODO - update timed events here (don't update on prev init)
        else:
            return '%s (init %s) is ready to act . . .' % (next[1], next[0],)

    def respondTo_p(self, user, _):
        """Previous initiative"""
        last, prev = self.initiatives.pop(-1), self.initiatives.pop(-1)
        self.initiatives.append(prev)
        self.initiatives.insert(0, last)
        if prev[1] is None:
            return '++ New round ++'
        else:
            return '%s (init %s) is ready to act . . .' % (prev[1], prev[0],)

    def respondTo_inits(self, user, _):
        """List inits, starting with the currently active character, in order"""
        # the "current" initiative is always at the end of the list
        if len(self.initiatives) > 0:
            current = self.initiatives[-1]
            inits = ['%s/%s' % (current[1], current[0])]
            for init in self.initiatives[:-1]:
                if init[1] is None:
                    name = 'NEW ROUND'
                else:
                    name = init[1]
                inits.append('%s/%s' % (name, init[0]))
            return 'Initiative list: ' + ', '.join(inits)
        else:
            return 'Initiative list: (none)'

    def respondTo_combat(self, user, _):
        """Start combat by resetting initiatives"""
        self.initiatives = [(9999, None)]
        return '** Beginning combat **'

