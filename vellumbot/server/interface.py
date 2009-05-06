"""
Zope interfaces used in vellumbot
"""

from zope.interface import Interface, Attribute


class ISessionResponse(Interface):
    """
    A source of messages to send to one or more channels, in response to a session
    action.
    """
    def getMessages():
        """
        @returns the messages as a list of 3-tuples: (recipient, message,
        encoding)
        """


class IMessageRecipient(Interface):
    """
    Someone to whom a message may be sent, including Sessions aka channels,
    and Users aka actors.
    """

    name = Attribute("""The name of the recipient, whether a channel or user""")
    encoding = Attribute("""The preferred encoding of the recipient, whether user or channel""")

