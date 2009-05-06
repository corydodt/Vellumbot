"""
Users and user acquisition
"""
from storm import locals
from zope.interface import implements

from .server.fs import fs
from .server.interface import IMessageRecipient


class User(object):
    """A User"""
    __storm_table__ = 'user'
    __storm_primary__ = ('name', 'network')
    name = locals.Unicode()       # nick of the user
    network = locals.Unicode(default=u'TODO FIXME')    # TODO - see vellumbot.server.irc.VellumTalk.signedOn
    encoding = locals.Unicode(default=u'utf-8')   # the preferred encoding of the user
    implements(IMessageRecipient)

    def __eq__(self, other):
        return (self.name, self.network) == (other.name, other.network)

    def __hash__(self):
        return hash((self.name, self.network))

    def __repr__(self):
        return '<%s named %s@%s>' % (self.__class__.__name__, self.name, self.network)

    def getAliases(self, default={}):
        """
        All the user's aliases as a dict
        """
        ret = {}
        for a in self.aliases:
            ret[a.words] = a.expression
        return ret

    def setAlias(self, words, expression):
        """
        Create a new alias for the user or redefine an existing
        """
        assert type(words) is tuple
        words = u' '.join(words)
        store = locals.Store.of(self)
        al = store.find(Alias, Alias.user==self, Alias.words==words).one()
        if al is None:
            al = Alias()
            al.user = self
            al.words = words
            al.expression = expression
            store.add(al)
        else:
            al.expression = expression
        store.commit()

    def removeAlias(self, words):
        """
        Remove an alias from my list and from the database
        """
        l = self.aliases.count()
        store = locals.Store.of(self)
        al = store.find(Alias, Alias.user==self, Alias.words==words).one()
        if al is not None:
            self.aliases.remove(al)
            store.remove(al)
            store.commit()
        assert store.find(Alias, 
                Alias.user==self, Alias.words==words).one() is None
        return al


class Alias(object):
    """
    A user-defined dice macro
    """
    __storm_table__ = 'alias'
    __storm_primary__ = ('userName', 'userNetwork', 'words')
    userName = locals.Unicode()
    userNetwork = locals.Unicode()
    words = locals.Unicode()
    expression = locals.Unicode()
    user = locals.Reference((userName, userNetwork), (User.name, User.network))

    def __repr__(self):
        return u'<Alias %s=%s of %r>' % (self.words, self.expression,
                self.user)

User.aliases = locals.ReferenceSet((User.name, User.network), 
        (Alias.userName, Alias.userNetwork))


DB_FILE_NAME = 'sqlite:' + fs.userdb

def parseURI(uri):
    """
    Return a (filename, uri) tuple from the URI, adding sqlite: if it was
    missing or removing it for the filename if it was present
    """
    if uri.startswith('sqlite:'):
        if uri[7:]:
            fn = uri[7:].strip()
            if fn.startswith('/'):
                fn = '/' + fn.lstrip('/')
        else:
            fn = None
    else:
        uri = 'sqlite:%s' % (uri,)
        fn = uri[7:]
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
    assert theStore is not None
    return theStore

