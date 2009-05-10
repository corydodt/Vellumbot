"""
Utilities for getting reference documentation
"""
from __future__ import with_statement

from contextlib import contextmanager


from goonmill import search, query
import hypy

@contextmanager
def openIndex(filename):
    estdb = hypy.HDatabase()
    estdb.open(search.INDEX_DIRECTORY, 'r')
    try:
        yield estdb
    finally:
        estdb.close()

DOMAINS = {
        u'monster': query.Monster,
        u'spell': query.Spell,
        }

def lookup(id, domain):
    """
    Get the database-backed Thing which corresponds to the domain and altname,
    mapping through DOMAINS to get the Thing's class as understood by
    playtools.query
    """
    return query.lookup(id, DOMAINS[domain])


def find(domain, terms, max=5):
    """
    Return either a list of teasers for the hits (up to max) or, if there is
    an exact match, the one-line description for that one
    """
    with openIndex(search.INDEX_DIRECTORY) as estdb:
        looked = search.find(estdb, domain, terms, max)
        ret = []
        normTerms = ' '.join(terms).lower()
        for look in looked:
            if look[u'altname'] == normTerms:
                _ignored_domain, id = look[u'@uri'].split(u'/')
                thing = lookup(int(id), domain)
                if thing:
                    return [thing.oneLineDescription()]
            ret.append('"%s": %s' % (look[u'altname'], look.teaser(terms,
                format='rst')))
        return ret
 
if __name__ == '__main__': 
    import sys
    args = sys.argv[:]
    args[1:1] = ['--index-dir', search.INDEX_DIRECTORY]
    sys.exit(
            search.run(args)
            )

