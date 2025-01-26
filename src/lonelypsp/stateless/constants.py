from enum import IntEnum, auto


class SubscriberToBroadcasterStatelessMessageType(IntEnum):
    """Assigns a unique integer to each type of message that a subscriber can
    send to a broadcaster over a stateless connection. The prototypical example
    of a stateless connection would be using a distinct HTTP call for each
    message. However, this protocol just requires that there is enough structure
    to have a fixed set of variable length headers (up to 2^16 bytes per header),
    a response status code (2 bytes), and a response body (up to 2^64 bytes). If
    the response status code is not 2xx, the response body has no guarranteed format,
    otherwise, it's as indicated

    Because stateless connections generally already have more parsing helpers available,
    we just provide documentation on how the message should be structured, but don't
    actually provide parsers or serializers.

    This avoids using non-standard http headers to reduce CORS issues, instead
    embedding e.g. what would naturally be x-tracing into the response
    """

    NOTIFY = auto()
    """The subscriber is posting a message to a specific topic
    
    ### headers
    - authorization: proof the subscriber is authorized to post to the topic

    ### request body
    - 2 bytes (N): length of the topic, big-endian, unsigned
    - N bytes: the topic. if utf-8 decodable then we will attempt to match glob
      patterns, otherwise, only goes to exact subscriptions
    - 64 bytes: sha-512 hash of the message, will be rechecked
    - 2 bytes (T): length of the tracing data, big-endian, unsigned
    - T bytes: the tracing data
    - 1 bytes (I): length of the identifier, big-endian, unsigned
    - I bytes: the identifier
    - 8 bytes (M): length of the message, big-endian, unsigned
    - M bytes: the message

    ### response body
    - `BroadcasterToSubscriberStatelessMessageType.RESPONSE_NOTIFY`
    """

    SUBSCRIBE_EXACT = auto()
    """The subscriber wants to receive messages posted to a specific topic. If
    the subscriber is already subscribed to the topic, the recovery url is ignored
    and no changes are made

    ### headers
    - authorization: proof the subscriber is authorized to subscribe to the topic

    ### request body
    - 2 bytes (N): length of the url that the subscriber can be reached at, big-endian, unsigned
    - N bytes: the url that the subscriber can be reached at, utf-8 encoded
    - 2 bytes (M): the length of the topic, big-endian, unsigned
    - M bytes: the topic
    - 2 bytes (R): either 0, to indicate no missed messages are desired, or the length
      of the url to post missed messages to, big-endian, unsigned
    - R bytes: the url to post missed messages to, utf-8 encoded
    - 2 bytes (T): length of the tracing data, big-endian, unsigned
    - T bytes: the tracing data

    ### response body
    - `BroadcasterToSubscriberStatelessMessageType.RESPONSE_GENERIC`
    """

    SUBSCRIBE_GLOB = auto()
    """The subscriber wants to receive messages to utf-8 decodable topics which match
    a given glob pattern. If the subscriber is already subscribed to the glob, the
    recovery url is ignored and no changes are made

    
    ### headers
    - authorization: proof the subscriber is authorized to subscribe to the pattern

    ### request body
    - 2 bytes (N): length of the url that the subscriber can be reached at, big-endian, unsigned
    - N bytes: the url that the subscriber can be reached at, utf-8 encoded
    - 2 bytes (M): the length of the glob pattern, big-endian, unsigned
    - M bytes: the glob pattern, utf-8 encoded
    - 2 bytes (R): either 0, to indicate no missed messages are desired, or the length
      of the url to post missed messages to, big-endian, unsigned
    - R bytes: the url to post missed messages to, utf-8 encoded
    - 2 bytes (T): length of the tracing data, big-endian, unsigned
    - T bytes: the tracing data
    
    ### response body
    - `BroadcasterToSubscriberStatelessMessageType.RESPONSE_GENERIC`
    """

    UNSUBSCRIBE_EXACT = auto()
    """The subscriber wants to stop receiving messages posted to a specific topic

    ### headers
    - authorization: proof the subscriber is authorized to unsubscribe from the topic;
      formed exactly like the authorization header in SUBSCRIBE_EXACT
    
    ### request body
    - 2 bytes (N): length of the url that the subscriber can be reached at, big-endian, unsigned
    - N bytes: the url that the subscriber can be reached at, utf-8 encoded
    - 2 bytes (M): the length of the topic, big-endian, unsigned
    - M bytes: the topic
    - 2 bytes (T): length of the tracing data, big-endian, unsigned
    - T bytes: the tracing data
    
    ### response body
    - `BroadcasterToSubscriberStatelessMessageType.RESPONSE_GENERIC`
    """

    UNSUBSCRIBE_GLOB = auto()
    """The subscriber wants to stop receiving messages to utf-8 decodable topics which match
    a given glob pattern

    ### headers
    - authorization: proof the subscriber is authorized to unsubscribe from the pattern;
      formed exactly like the authorization header in SUBSCRIBE_GLOB

    ### request body
    - 2 bytes (N): length of the url that the subscriber can be reached at, big-endian, unsigned
    - N bytes: the url that the subscriber can be reached at, utf-8 encoded
    - 2 bytes (M): the length of the glob pattern, big-endian, unsigned
    - M bytes: the glob pattern, utf-8 encoded
    - 2 bytes (T): length of the tracing data, big-endian, unsigned
    - T bytes: the tracing data
    
    ### response body
    - `BroadcasterToSubscriberStatelessMessageType.RESPONSE_GENERIC`
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
    - 2 bytes (T): length of the tracing data, big-endian, unsigned
    - T bytes: the tracing data
    - 2 bytes (N): length of the subscriber url to check, big-endian, unsigned
    - N bytes: the url to check, utf-8 encoded

    ### response body
    -  `BroadcasterToSubscriberStatelessMessageType.RESPONSE_CHECK_SUBSCRIPTIONS`
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
    - 2 bytes (T): length of tracing data, big-endian, unsigned
    - T bytes: the tracing data
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
    - `BroadcasterToSubscriberStatelessMessageType.RESPONSE_GENERIC`
    """

    RESPONSE_CONFIRM_RECEIVE = auto()
    """The subscriber is confirming that it received a message from a broadcaster
    over a stateless connection. This primarily provides tracing data back to
    the broadcaster

    ### response body
    - 2 bytes (type): int(RESPONSE_CONFIRM_RECEIVE), big endian, unsigned
    - 2 bytes (A): length of authorization, big-endian, unsigned
    - A bytes: authorization, utf-8 encoded
    - 2 bytes (T): length of tracing data, big-endian, unsigned
    - T bytes: tracing data
    - 1 byte (I): length of the identifier, big-endian, unsigned
    - I bytes: the identifier
    - 4 bytes (N): the number of subscribers, big-endian, unsigned. usually
      1 but can be more if this subscriber forwarded the message to others
    """

    RESPONSE_CONFIRM_MISSED = auto()
    """If the broadcaster reaches out to a subscriber that it missed a message on
    a topic, the subscriber can respond in the same connection that it received
    the message. This primarily provides tracing data back to the broadcaster
    
    ### response body
    - 2 bytes (type): int(RESPONSE_CONFIRM_MISSED), big endian, unsigned
    - 2 bytes (A): length of authorization, big-endian, unsigned
    - A bytes: authorization, utf-8 encoded
    - 2 bytes (T): length of tracing data, big-endian, unsigned
    - T bytes: tracing data
    """

    RESPONSE_UNSUBSCRIBE_IMMEDIATE = auto()
    """If the broadcaster reaches out to a subscriber, the subscriber can respond in
    the same connection that it wants to unsubscribe without authorization. This
    does mean that when using a non-verifying protocol (e.g., plain http), a
    middleman can unsubscribe the subscriber from the broadcaster, but it also
    allows for recovery in a much broader set of scenarios.

    ### response body
    - 2 bytes (type): int(RESPONSE_UNSUBSCRIBE_IMMEDIATE), big endian, unsigned
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

    ### request body
    - 2 bytes (T): length of the tracing data, big-endian, unsigned
    - T bytes: the tracing data
    - 2 bytes (N): length of the topic, big-endian, unsigned
    - N bytes: the topic
    - 1 byte (I): length of the identifier, big-endian, unsigned
    - I bytes: the identifier
    - 8 bytes (M): length of the message, big-endian, unsigned
    - M bytes: the message

    ### response body
    any of:
    - `SubscriberToBroadcasterStatelessMessageType.RESPONSE_CONFIRM_RECEIVE`
    - `SubscriberToBroadcasterStatelessMessageType.RESPONSE_UNSUBSCRIBE_IMMEDIATE`
    """

    MISSED = auto()
    """The broadcaster is notifying the subscriber they previously failed to send
    a message to the subscriber about a message on a topic the subscriber was
    subscribed to. This is an important primitive for using persistent topics
    via log channels.

    ### headers
    - authorization: proof the broadcaster can notify the subscriber

    ### request body
    - 2 bytes (T): length of the tracing data, big-endian, unsigned
    - T bytes: the tracing data
    - 2 bytes (N): length of the topic, big-endian, unsigned
    - N bytes: the topic

    ### response body
    """

    RESPONSE_GENERIC = auto()
    """
    The generic response from the broadcaster when no special data is required

    - 2 bytes (type): int(RESPONSE_GENERIC), big endian, unsigned
    - 2 bytes (A): big-endian, unsigned, the length of the authorization
    - A bytes: the authorization
    - 2 bytes (T): big-endian, unsigned, the length of tracing data
    - T bytes: the tracing data
    """

    RESPONSE_NOTIFY = auto()
    """
    The response the broadcaster sends to a subscriber after receiving a NOTIFY
    
    - 2 bytes (type): int(RESPONSE_NOTIFY), big endian, unsigned
    - 2 bytes (A): big-endian, unsigned, the length of the authorization. broadcaster
      side authorization is always used because hmac over http is supported
    - A bytes: the authorization
    - 2 bytes (T): big-endian, unsigned, the length of tracing data
    - T bytes: the tracing data
    - 4 bytes: big-endian, unsigned, the number of subscribers notified
    - 1 byte (I): length of the identifier, big-endian, unsigned
    - I bytes: the identifier
    """

    RESPONSE_CHECK_SUBSCRIPTIONS = auto()
    """The response the broadcaster sends to a subscriber after receiving a CHECK_SUBSCRIPTIONS

    - 2 bytes (type): int(RESPONSE_CHECK_SUBSCRIPTIONS), big endian, unsigned
    - 2 bytes (A): big-endian, unsigned, the length of the authorization
    - A bytes: the authorization
    - 2 bytes (T): big-endian, unsigned, the length of tracing data
    - T bytes: the tracing data
    - 1 byte (reserved for etag format): 0
    - 64 bytes: the etag
    """
