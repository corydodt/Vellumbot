"""
Utilities for getting reference documentation
"""
from __future__ import with_statement

from contextlib import contextmanager


from playtools import search, fact
from . import _formattingkludge
import hypy

SRD = fact.systems['D20 SRD']

@contextmanager
def openIndex(filename):
    estdb = hypy.HDatabase()
    estdb.open(search.INDEX_DIRECTORY, 'r')
    try:
        yield estdb
    finally:
        estdb.close()


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
                thing = SRD.facts[domain].lookup(int(id))
                if thing:
                    return [_formattingkludge.IOneLine(thing).format()]
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

