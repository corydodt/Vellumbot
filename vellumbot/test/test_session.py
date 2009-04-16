
from twisted.trial import unittest

from ..server.irc import Request
from ..server import session


class ResponseTestCase(unittest.TestCase):
    def setUp(self):
        self.req = Request('Player', '#testing', '.hello')

    def test_normalMessaging(self):
        """
        Messages get generated
        """
        self.req.setRecipients('Player')
        resp = session.Response("whatever", self.req)
        self.assertEqual(list(resp.getMessages()), 
                [('Player', 'whatever')])

    def test_noRecipients(self):
        self.assertRaises(session.MissingRecipients, session.Response,
                "whatever", self.req)

    def test_multiMessaging(self):
        """
        Messages with more recipients get generated
        """
        self.req.setRecipients('Player', 'GeeEm', 'GeeEm2')
        resp1 = session.Response("whatever", self.req, redirectTo=None)
        self.assertEqual(list(resp1.getMessages()), 
                [('Player', 'whatever (observed)'),
                 ('GeeEm', 'whatever (<Player>  .hello)'),
                 ('GeeEm2', 'whatever (<Player>  .hello)'),
                 ])

        self.req.setRecipients('#testing', 'GeeEm', 'GeeEm2')
        resp2 = session.Response("whatever", self.req, redirectTo=None)
        self.assertEqual(list(resp2.getMessages()), 
                [('#testing', 'whatever (observed)'),
                 ('GeeEm', 'whatever (<Player>  .hello)'),
                 ('GeeEm2', 'whatever (<Player>  .hello)'),
                 ])

    def test_redirectMessaging(self):
        """
        Redirected messages go to some other person
        """
        self.req.setRecipients('#testing')
        resp1 = session.Response("whatever", self.req, redirectTo='Player')
        self.assertEqual(list(resp1.getMessages()), 
                [('Player', 'whatever'),
                 ])

        # redirectTo redirects only the PRIMARY recipient's message, i.e. the
        # first argument.  all other recipients still get whatever they would
        # get.
        self.req.setRecipients('#testing', 'GeeEm')
        resp2 = session.Response("whatever", self.req, redirectTo='Player')
        self.assertEqual(list(resp2.getMessages()), 
                [('Player', 'whatever (observed)'),
                 ('GeeEm', 'whatever (<Player>  .hello)'),
                 ])


class ResponseGroupTestCase(unittest.TestCase):
    def setUp(self):
        self.req = Request('Player', '#testing', '.hello')

    def test_responseKinds(self):
        self.req.setRecipients('Player', 'GeeEm')
        r1 = session.Response('whatever 1', self.req)
        r2 = session.Response('whatever 2', self.req)
        # init with responses
        rg = session.ResponseGroup(r1, r2)
        l = lambda r: list(r.getMessages())

        expected = [('Player', 'whatever 1 (observed)'),
                 ('GeeEm', 'whatever 1 (<Player>  .hello)'),
                 ('Player', 'whatever 2 (observed)'),
                 ('GeeEm', 'whatever 2 (<Player>  .hello)'),
                 ]

        self.assertEqual(l(rg), expected)

        # add responses - textual
        rg = session.ResponseGroup()
        rg.addResponse(['whatever 1', self.req])
        rg.addResponse(['whatever 2', self.req])
        self.assertEqual(l(rg), expected)

        # add responses - response objects
        rg = session.ResponseGroup()
        rg.addResponse(r1)
        rg.addResponse(r2)
        self.assertEqual(l(rg), expected)



class SessionTestCase(unittest.TestCase):
    pass
