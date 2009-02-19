"""
Utilities for getting reference documentation
"""
from __future__ import with_statement

from contextlib import contextmanager

from vellumbot.server.fs import fs

from goonmill import search, query
import hypy

@contextmanager
def openIndex(filename):
    estdb = hypy.HDatabase()
    estdb.open(fs.hypy('.'), 'r')
    try:
        yield estdb
    finally:
        estdb.close()

DOMAINS = {'monster': query.Monster,
        'spell': query.Spell,
        }


def find(domain, terms, max=5):
    """
    Return either a list of teasers for the hits (up to max) or, if there is
    an exact match, the one-line description for that one
    """
    with openIndex(fs.hypy('')) as estdb:
        looked = search.find(estdb, domain, terms, max)
        ret = []
        normTerms = ' '.join(terms).lower()
        for look in looked:
            if look[u'altname'] == normTerms:
                thing = query.lookup(look[u'altname'], DOMAINS[domain])
                if thing:
                    return [thing.oneLineDescription()]
            ret.append('"%s": %s' % (look[u'altname'], look.teaser(terms,
                format='rst')))
        return ret
 
if __name__ == '__main__': 
    import sys
    args = sys.argv[:]
    args[1:1] = ['--index-dir', fs.hypy('.')]
    sys.exit(
            search.run(args)
            )

