"""
Users and user acquisition
"""
from storm import locals

from .server.fs import fs


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
    user = locals.Reference(userId, User.id)

User.aliases = locals.ReferenceSet( User.id, Alias.userId,)


DB_FILE_NAME = 'sqlite:' + fs.userdb

def parseURI(uri):
    """
    Return a (filename, uri) tuple from the URI, adding sqlite: if it was
    missing or removing it for the filename if it was present
    """
    if uri.startswith('sqlite:'):
        if uri[7:]:
            fn = '/' + uri[7:].strip().lstrip('/')
        else:
            fn = None
    else:
        uri = 'sqlite:%s' % (uri,)
        fn = uri
    return (fn, uri)

def userDatabase(uri=DB_FILE_NAME):
    """
    Give a user database
    """
    filename, uri = parseURI(uri)
    db = locals.create_database(uri)
    if filename is not None:
        # test existence of the database file so as to throw an exception when
        # the bootstrap script was not run.  Test it before creating the Store
        # because creating the Store creates the file whether it makes sense
        # to or not.
        open(filename).close()
        theStore = locals.Store(db)
    else:
        theStore = locals.Store(db)
        from .usersql import SQL_SCRIPT
        for sql in SQL_SCRIPT:
            theStore.execute(sql)
    return theStore

