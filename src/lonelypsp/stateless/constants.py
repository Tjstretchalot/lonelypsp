from enum import IntEnum, auto


class SubscriberToBroadcasterStatelessMessageType(IntEnum):
    """Assigns a unique integer to each type of message that a subscriber can
    send to a broadcaster over a stateless connection. The prototypical example
    of a stateless connection would be using a distinct HTTP call for each
    message.

    Because stateless connections generally already have more parsing helpers available,
    we just provide documentation on how the message should be structured, but don't
    actually provide parsers or serializers.
    """

    NOTIFY = auto()
    """The subscriber is posting a message to a specific topic
    
    ### headers
    - authorization: proof the subscriber is authorized to post to the topic

    ### body
    - 2 bytes (N): length of the topic, big-endian, unsigned
    - N bytes: the topic. if utf-8 decodable then we will attempt to match glob
      patterns, otherwise, only goes to exact subscriptions
    - 64 bytes: sha-512 hash of the message, will be rechecked
    - 8 bytes (M): length of the message, big-endian, unsigned
    - M bytes: the message
    """

    SUBSCRIBE_EXACT = auto()
    """The subscriber wants to receive messages posted to a specific topic. If
    the subscriber is already subscribed to the topic, the recovery url is ignored
    and no changes are made

    ### headers
    - authorization: proof the subscriber is authorized to subscribe to the topic

    ### body
    - 2 bytes (N): length of the url that the subscriber can be reached at, big-endian, unsigned
    - N bytes: the url that the subscriber can be reached at, utf-8 encoded
    - 2 bytes (M): the length of the topic, big-endian, unsigned
    - M bytes: the topic, utf-8 encoded
    - 2 bytes (R): either 0, to indicate no missed messages are desired, or the length
      of the url to post missed messages to, big-endian, unsigned
    - R bytes: the url to post missed messages to, utf-8 encoded
    """

    SUBSCRIBE_GLOB = auto()
    """The subscriber wants to receive messages to utf-8 decodable topics which match
    a given glob pattern. If the subscriber is already subscribed to the glob, the
    recovery url is ignored and no changes are made

    
    ### headers
    - authorization: proof the subscriber is authorized to subscribe to the pattern

    ### body
    - 2 bytes (N): length of the url that the subscriber can be reached at, big-endian, unsigned
    - N bytes: the url that the subscriber can be reached at, utf-8 encoded
    - 2 bytes (M): the length of the glob pattern, big-endian, unsigned
    - M bytes: the glob pattern, utf-8 encoded
    - 2 bytes (R): either 0, to indicate no missed messages are desired, or the length
      of the url to post missed messages to, big-endian, unsigned
    - R bytes: the url to post missed messages to, utf-8 encoded
    """

    UNSUBSCRIBE_EXACT = auto()
    """The subscriber wants to stop receiving messages posted to a specific topic

    ### headers
    - authorization: proof the subscriber is authorized to unsubscribe from the topic;
      formed exactly like the authorization header in SUBSCRIBE_EXACT
    
    ### body
    - 2 bytes (N): length of the url that the subscriber can be reached at, big-endian, unsigned
    - N bytes: the url that the subscriber can be reached at, utf-8 encoded
    - 2 bytes (M): the length of the topic, big-endian, unsigned
    - M bytes: the topic, utf-8 encoded
    """

    UNSUBSCRIBE_GLOB = auto()
    """The subscriber wants to stop receiving messages to utf-8 decodable topics which match
    a given glob pattern

    ### headers
    - authorization: proof the subscriber is authorized to unsubscribe from the pattern;
      formed exactly like the authorization header in SUBSCRIBE_GLOB

    ### body
    - 2 bytes (N): length of the url that the subscriber can be reached at, big-endian, unsigned
    - N bytes: the url that the subscriber can be reached at, utf-8 encoded
    - 2 bytes (M): the length of the glob pattern, big-endian, unsigned
    - M bytes: the glob pattern, utf-8 encoded
    """

    CHECK_SUBSCRIPTIONS = auto()
    """The subscriber wants to get the strong etag representing the subscriptions for
    a specific url. Generally, the subscriber is comparing it against what it
    expects by computing it itself.

    The strong etag is the SHA512 hash of a document which is of the following
    form, where all indicated lengths are 2 bytes, big-endian encoded:
    
    ```
    URL<url_length><url>
    EXACT<topic_length><topic><recovery_length><recovery><...>
    GLOB<glob_length><glob><recovery_length><recovery><...>
    ```

    where URL, EXACT and GLOB are the ascii-representations and there
    are 3 guarranteed newlines as shown (including a trailing newline). Note
    that URL, EXACT, GLOB, and newlines may show up within
    topics/globs. The topics and globs must be sorted in (bytewise)
    lexicographical order

    ### headers
    - authorization: proof the subscriber is authorized to check the subscriptions for the url

    ### request body
    - 2 bytes (N): length of the subscriber url to check, big-endian, unsigned
    - N bytes: the url to check, utf-8 encoded

    ### response body
    - 1 byte (reserved for etag format): 0
    - 64 bytes: the etag
    """

    SET_SUBSCRIPTIONS = auto()
    """The subscriber wants to set all of their subscriptions and retrieve the strong etag
    it corresponds to. Unlike with `SUBSCRIBE`/`UNSUBSCRIBE`, this message is idempotent, which
    makes recovery easier. 

    The broadcaster MUST guarrantee the following properties, which mostly
    apply to concurrent requests:

    - If the subscriber is previously subscribed to a topic/glob and that
      topic/glob is in this list, the subscriber is at no point unsubscribed
      from that topic/glob due to this call
    - If the subscriber is not previously subscribed to a topic/glob and that
      is not in this list, the subscriber is at no point subscribed to that
      topic/glob due to this call
    - At some point during this call, the subscriber is subscribed to each
      (but not necessarily all) of the topics/globs in this list
    - At some point during this call, the subscriber is unsubscribed from
      each (but not necessarily all) of the topics/globs not in this list

    See the documentation for `CHECK_SUBSCRIPTIONS` for the format of the etag

    ### headers
    - authorization: proof the subscriber is authorized to set the subscriptions for the url

    ### request body
    - 2 bytes (N): length of the subscriber url to set, big-endian, unsigned
    - N bytes: the url to set, utf-8 encoded
    - 1 byte (reserved for etag format): 0
    - 64 bytes: the strong etag, will be rechecked
    - 4 bytes (E): the number of exact topics to set, big-endian, unsigned
    - REPEAT E TIMES: (in ascending lexicographic order of the topics)
      - 2 bytes (L): length of the topic, big-endian, unsigned
      - L bytes: the topic
      - 2 bytes (R): the length of the recovery url, big-endian, unsigned,
        may be 0 for no recovery url
      - R bytes: the recovery url, utf-8 encoded
    - 4 bytes (G): the number of glob patterns to set, big-endian, unsigned
    - REPEAT G TIMES: (in ascending lexicographic order of the globs)
      - 2 bytes (L): length of the glob pattern, big-endian, unsigned
      - L bytes: the glob pattern, utf-8 encoded
      - 2 bytes (R): the length of the recovery url, big-endian, unsigned,
        may be 0 for no recovery url
      - R bytes: the recovery url, utf-8 encoded

    ### response body
    empty
    """


class SubscriberToBroadcasterStatelessResponseType(IntEnum):
    """When the broadcaster reaches out to a subscriber they have the opportunity
    to respond with one of these types of messages, without headers
    """

    UNKNOWN = auto()
    """Used when no specific meaning was understood about the response"""

    UNSUBSCRIBE_IMMEDIATE = auto()
    """When sent in response to a RECEIVE message, removes whatever subscription
    caused the subscriber to receive the message

    The body is a json object with at least the following keys:
    - `unsubscribe`: the value `true`

    All other values are ignored, however, a common one worth mentioning is:
    - `reason`: a human-readable string indicating if the subscriber didn't
      like the format of the message vs just wasn't expecting a message on that
      topic vs was expecting the message but no longer wants more
    """


class BroadcasterToSubscriberStatelessMessageType(IntEnum):
    """Assigns a unique integer to each type of message that a broadcaster can
    send to a subscriber over a stateless connection. The prototypical example
    of a stateless connection would be using a distinct HTTP call for each
    message.
    """

    RECEIVE = auto()
    """The broadcaster is notifying the subscriber of a message posted to a topic
    
    ### headers
    - authorization: proof the broadcaster can notify the subscriber
    - repr-digest: contains <digest-algorithm>=<digest>[,<digest-algorithm>=<digest>...]
      where at least one of the digest algorithms is `sha512` and the digest is the
      the base64 encoded sha-512 hash of the message
    - x-topic: the topic the message was posted to

    ### body
    the message that was posted to the topic
    """

    MISSED = auto()
    """The broadcaster is notifying the subscriber they previously failed to send
    a message to the subscriber about a message on a topic the subscriber was
    subscribed to. This is an important primitive for using persistent topics
    via log channels.

    ### headers
    - authorization: proof the broadcaster can notify the subscriber
    - x-topic: the topic the message was posted to

    ### body
    none
    """
