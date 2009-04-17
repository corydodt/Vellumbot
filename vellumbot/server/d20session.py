"""Session subclass specific to D20 (inits etc.)"""

from collections import deque
import bisect

from vellumbot.server import alias, session, reference

class D20Session(session.Session):
    def __init__(self, channel):
        session.Session.__init__(self, channel)
        self.initiatives = []
        alias.registerAliasHook(('init',), self.doInitiative)

    def _lookup_anything(self, req, terms, domain):
        assert type(domain) is unicode
        UPPER = domain.upper()
    
        ts = u' '.join(k.decode('utf-8') for k in terms)
        looked = reference.find(domain, [ts])
        if not looked:
            if '*' in ts:
                return '%s: No %s contains "%s".' % (req.user, UPPER, ts,)
            else:
                return (
                    '%s: No %s contains "%s".  Try searching with a wildcard e.g. .lookup %s %s*' % (
                            req.user, UPPER, ts, domain, ts))
        else:
            if looked[0].startswith('<<'):
                assert len(looked) == 1, "Exact match returned with %s hits?" % ( len(looked), )
                return '%s: %s %s' % (req.user, UPPER, looked[0])
            else:
                rg = session.ResponseGroup()

                for line in looked:
                    rg.addResponse(session.Response(line, req,
                        redirectTo=req.user))

                count = len(looked)
                m = 'Replied to %s with top %s matches for SPELL "%s"' % (req.user, count, ts)

                rg.addResponse([m, req])

                return rg

    def lookup_monster(self, req, terms):
        """
        Look up a spell and say what it is
        """
        return self._lookup_anything(req, terms, u'monster')

    def lookup_spell(self, req, terms):
        """
        Look up a spell and say what it is
        """
        return self._lookup_anything(req, terms, u'spell')

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


class SortedRing(object):
    """
    A sequence data structure which retains a canonical order and also has a
    ring looping mechanism.
    """
    def __init__(self, items=None):
        if items is None:
            self.rotation = 0
            self.items = []
        else:
            self.items = sorted(items)
            self.rotation = 0

    def __getitem__(self, n):
        return self.items[n]

    def addSorted(self, item):
        """
        Insert item into the items, keeping sort
        """
        bisect.insort_right(self.items, item)
        if self.items.index(item) < self.rotation:
            self.rotation = self.rotation + 1

    def index(self, item):
        return self.items.index(item)

    def rotate(self, n=None):
        """
        Rotate the ring by n (like deque.rotate)
        """
        if n is None:
            n = 1
        rot = (self.rotation + n) % len(self.items)
        self.rotation = rot

    def __delitem__(self, n):
        del self.items[n]
        if self.rotation > len(self.items):
            self.rotation = 0

    def __len__(self):
        return len(self.items)

    def current(self):
        rot = self.rotation
        return self.items[rot]

    def next(self):
        rot = self.rotation + 1
        if rot > (len(self)-1):
            n = 0
        else:
            n = rot
        return self.items[n]

    def prev(self):
        rot = self.rotation - 1
        if rot < 0:
            p = -1
        else:
            p = rot
        return self.items[p]
