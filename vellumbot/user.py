"""
Users and user acquisition
"""
from storm import locals

from .util import fs

class User(object):
    """A User"""
    __storm_table__ = 'user'
    id = locals.Int(primary=True)                #
    name = locals.Unicode()


class Alias(object):
    """
    A user-defined dice macro
    """
    __storm_table__ = 'alias'
    __storm_primary__ = ('userId', 'words')
    userId = locals.Int()
    words = locals.Unicode()
    expression = locals.Unicode()

User.aliases = locals.ReferenceSet( User.id, Alias.userId,)


# the global store object. yay, global mutable state!
theStore = None


def userDatabase():
    """Give a user database"""
    global theStore
    if theStore is not None:
        raise RuntimeError("Already created a db store")
    db = locals.create_database('sqlite:///' + fs('user.db'))
    theStore = locals.Store(db)
    return theStore

