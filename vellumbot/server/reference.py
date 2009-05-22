"""
Utilities for getting reference documentation
"""
from __future__ import with_statement

from contextlib import contextmanager

from playtools import search, fact, publish

import hypy

# FIXME!! have to import this otherwise publishers are not registered
from . import oneline
oneline

SRD = fact.systems['D20 SRD']

@contextmanager
def openIndex(filename):
    estdb = hypy.HDatabase()
    estdb.open(SRD.searchIndexPath, 'r')
    try:
        yield estdb
    finally:
        estdb.close()


def find(domain, terms, max=5):
    """
    Return either a list of teasers for the hits (up to max) or, if there is
    an exact match, the one-line description for that one
    """
    with openIndex(SRD.searchIndexPath) as estdb:
        looked = search.find(estdb, domain, terms, max)
        ret = []
        normTerms = ' '.join(terms).lower()
        for look in looked:
            if look[u'altname'] == normTerms:
                _ignored_domain, id = look[u'@uri'].split(u'/', 1)
                thing = SRD.facts[domain].lookup(id)
                if thing:
                    return [u"EXACT: %s" % (publish.publish(thing, 'richIRC'),)]
            ret.append('"%s": %s' % (look[u'altname'], look.teaser(terms,
                format='rst')))
        return ret
 
