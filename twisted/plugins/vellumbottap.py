"""
Twistd plugin to run Vellumbot
"""

from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker

class Options(usage.Options):
    optParameters = [['port', 'p', '6667', 'Port to connect to'],
                     ['server', 's', 'irc.freenode.net', 'IRC server to connect to'],
                     ]
    optFlags = [['dev', None, 'Enable development features such as /sandbox']]


class VellumbotServerMaker(object):
    """
    Framework boilerplate class: This is used by twistd to get the service
    class.

    Basically exists to hold the IServiceMaker interface so twistd can find
    the right makeService method to call.
    """
    implements(IServiceMaker, IPlugin)
    tapname = "vellumbot"
    description = "The Vellum dice bot"
    options = Options

    def makeService(self, options):
        """
        Construct the vellumbot
        """
        if options['dev']:
            try:
                import wingdbstub
            except ImportError:
                pass
        from vellumbot.server.irc import VellumTalkFactory
        from twisted.application.internet import TCPClient
        f = VellumTalkFactory('#vellum')
        svc = TCPClient(options['server'], int(options['port']), f)
        return svc

# Now construct an object which *provides* the relevant interfaces

# The name of this variable is irrelevant, as long as there is *some*
# name bound to a provider of IPlugin and IServiceMaker.

serviceMaker = VellumbotServerMaker()
