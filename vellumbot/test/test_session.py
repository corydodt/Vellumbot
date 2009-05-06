
from twisted.trial import unittest

from ..server.irc import Request
from ..server import session
from . import util
from .. import user

class UserAddingTestMixin(object):
    """
    Provide a user store to work with, and addUser

    Make sure to upcall setUp
    """
    def setUp(self):
        self.store = user.userDatabase('sqlite:')

    def addUser(self, name):
        """
        Convenience to add and return a user
        """
        u = user.User()
        u.name = name
        self.store.add(u)
        self.store.commit()
        return u


class ResponseTestCase(unittest.TestCase, UserAddingTestMixin):
    def setUp(self):
        self.req = Request('Player', '#testing', '.hello')
        UserAddingTestMixin.setUp(self)

    def test_normalMessaging(self):
        """
        Messages get generated
        """
        player = self.addUser(u'Player')
        self.req.setRecipients(player)
        resp = session.Response("whatever", self.req)
        self.assertEqual(list(resp.getMessages()), 
                [(player, 'whatever', 'utf-8')])

    def test_noRecipients(self):
        self.assertRaises(session.MissingRecipients, session.Response,
                "whatever", self.req)

    def test_multiMessaging(self):
        """
        Messages with more recipients get generated
        """
        player = self.addUser(u'Player')
        gm = self.addUser(u'GeeEm')
        gm2 = self.addUser(u'GeeEm2')

        self.req.setRecipients(player, gm, gm2)
        resp1 = session.Response("whatever", self.req, redirectTo=None)
        self.assertEqual(list(resp1.getMessages()), 
                [(player, 'whatever (observed)', 'utf-8'),
                 (gm, '<Player>  .hello  ===>  whatever', 'utf-8'),
                 (gm2, '<Player>  .hello  ===>  whatever', 'utf-8'),
                 ])

        _testing = session.Session(); _testing.name = u'#testing'
        self.req.setRecipients(_testing, gm, gm2)
        resp2 = session.Response("whatever", self.req, redirectTo=None)
        self.assertEqual(list(resp2.getMessages()), 
                [(_testing, 'whatever (observed)', 'utf-8'),
                 (gm, '<Player>  .hello  ===>  whatever', 'utf-8'),
                 (gm2, '<Player>  .hello  ===>  whatever', 'utf-8'),
                 ])

    def test_redirectMessaging(self):
        """
        Redirected messages go to some other person
        """
        _testing = session.Session(); _testing.name = u'#testing'
        player = self.addUser(u'Player')
        gm = self.addUser(u'GeeEm')

        self.req.setRecipients(_testing)
        resp1 = session.Response("whatever", self.req, redirectTo=player)
        self.assertEqual(list(resp1.getMessages()), 
                [(player, 'whatever', 'utf-8'), ]
            )

        # redirectTo redirects only the PRIMARY recipient's message, i.e. the
        # first argument.  all other recipients still get whatever they would
        # get.
        self.req.setRecipients(_testing, gm)
        resp2 = session.Response("whatever", self.req, redirectTo=player)
        self.assertEqual(list(resp2.getMessages()), 
                [(player, 'whatever (observed)', 'utf-8'),
                 (gm, '<Player>  .hello  ===>  whatever', 'utf-8'),
                 ])


class ResponseGroupTestCase(unittest.TestCase, UserAddingTestMixin):
    def setUp(self):
        self.req = Request('Player', '#testing', '.hello')
        UserAddingTestMixin.setUp(self)

    def test_responseKinds(self):
        """
        Ensure that responseGroups are checking that only Responses are
        provided as an argument to addResponse
        """
        player = self.addUser(u'Player')
        gm = self.addUser(u'GeeEm')
        self.req.setRecipients(player, gm)
        r1 = session.Response('whatever 1', self.req)
        r2 = session.Response('whatever 2', self.req)
        # init with responses
        rg = session.ResponseGroup(r1, r2)
        l = lambda r: list(r.getMessages())

        expected = [(player, 'whatever 1 (observed)', 'utf-8'),
                 (gm, '<Player>  .hello  ===>  whatever 1', 'utf-8'),
                 (player, 'whatever 2 (observed)', 'utf-8'),
                 (gm, '<Player>  .hello  ===>  whatever 2', 'utf-8'),
                 ]

        self.assertEqual(l(rg), expected)

        # add responses - textual (this is no longer allowed - test for
        # assertion)
        rg = session.ResponseGroup()
        self.assertRaises(AssertionError, rg.addResponse, ['whatever 1', self.req])

        # add responses - response objects
        rg = session.ResponseGroup()
        rg.addResponse(r1)
        rg.addResponse(r2)
        self.assertEqual(l(rg), expected)


class SessionTestCase(util.BotTestCase):
    pass
