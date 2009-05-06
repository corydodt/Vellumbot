"""Session subclass specific to D20 (inits etc.)"""

from collections import deque
import bisect

from storm import locals

from vellumbot.server import alias, session, reference


class InitRoll(object):
    """
    An initiative roll, sortable descending
    """
    def __init__(self, n, user):
        self.n = n
        self.user = user

    def __cmp__(self, other):
        return -cmp(self.n, other.n)

    def __str__(self):
        if self.user is None:
            return "new round"
        return "%s (%s)" % (self.user, self.n)


class D20Session(session.Session):
    def __init__(self, isDefaultSession=False):
        session.Session.__init__(self, isDefaultSession)
        self.initiatives = SortedRing()
        alias.registerAliasHook(('init',), self.doInitiative)

    __storm_loaded__ = __init__  

    def doInitiative(self, user, result):
        self.initiatives.addSorted(InitRoll(result[0].sum(), user.name))

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
                    ss = self._nameToRecipient(req.user)
                    rg.addResponse(session.Response(line, req, redirectTo=ss))

                count = len(looked)
                m = 'Replied to %s with top %s matches for SPELL "%s"' % (req.user, count, ts)

                rg.addResponse(session.Response(m, req))

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

    def _formatThisRound(self):
        cur = self.initiatives.current()
        n = self.initiatives.next()

        if cur.user is None:
            return '++ New round ++  Next: %s.' % ( n,)
            # TODO - update timed events here (don't update on prev init)
        else:
            return 'GOING NOW: %s!  Next: %s.' % ( cur, n)

    def respondTo_n(self, user, actor, _):
        """Next initiative"""
        self.initiatives.rotate()
        return self._formatThisRound()

    def respondTo_p(self, user, actor, _):
        """Previous initiative"""
        self.initiatives.rotate(-1)
        return self._formatThisRound()

    def respondTo_inits(self, user, actor, _):
        """List inits, starting with the currently active character, in order"""
        if len(self.initiatives) > 0:
            rotated = self.initiatives.asRotatedList()
            inits = []
            for init in rotated:
                if init.user is None:
                    s = 'new round'
                else:
                    s = '%s/%s' % (init.user, init.n)
                inits.append(s)
            return 'INITIATIVES: ' + ' || '.join(inits)
        else:
            return 'INITIATIVES: (none)'

    def respondTo_combat(self, user, actor, _):
        """Start combat by resetting initiatives"""
        self.initiatives = SortedRing([InitRoll(9999, None)])
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

    def asRotatedList(self):
        """
        List of all the items, oriented by rotation.  In other words,
        beginning from current() and counting to the right, return all items.
        """
        rot = self.rotation
        l = self[rot:]
        rest = self[:rot]
        return l + rest
