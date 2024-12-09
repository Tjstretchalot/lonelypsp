from enum import IntFlag, auto


class SubscriberToBroadcasterStatelessMessageType(IntFlag):
    """Assigns a unique integer to each type of message that a subscriber can
    send to a broadcaster over a stateless connection
    """

    NOTIFY = auto()
    """The subscriber is posting a message to a specific topic"""
