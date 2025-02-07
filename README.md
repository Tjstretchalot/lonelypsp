# lonelypsp

Lonely Pub-Sub Protocol (lonely being the opposite of connected!)

## PROJECT STAGE - PRE ALPHA

This project is in the development stage 2 - pre-alpha. There is some testing in
the [`lonelypst`](https://github.com/Tjstretchalot/lonelypst) repository, but
there are constant sweeping changes that break the api still ongoing to
facilitate all the desired functionality

## Overview

This is the Python specification for the protocol used by the canonical implementation
[lonelypss](https://github.com/Tjstretchalot/lonelypss). It serves both
as a reference for the protocol and as a helper library for the Python server and client.

The types here are intended to facilitate alternate server and client
implementations in a variety of languages, such as Ruby, TypeScript, and Rust.

This library is fully mypy checked and has a flat class heirarchy (no
subclasses); as soon as you check e.g. the type field, mypy and pylance will be
able to deduce specific and accurate information about the remaining fields.

This library is designed intentionally so you can pick and choose any part of the
implementation to use relatively painlessly.

Although the message packets are named for the initial transport layer (websockets),
they will work in any reliable protocol where every message below a known size > 1024 bytes is
not fragmented and the total length of the message is known. Thus, it can used directly
on TCP with a bit of buffering and framing the message length for a significant
performance boost compared to websockets (mostly due to not having to mask the data).

## Usage

Parsing:

```python
import io

from lonelypsp.stateful.parser import S2B_AnyMessageParser
from lonelypsp.stateful.parser_helpers import parse_s2b_message_prefix


message_body: io.BytesIO = ...
prefix = parse_s2b_message_prefix(message_body)
message = S2B_AnyMessageParser.parse(prefix.flags, prefix.type, message_body)

if message.type == SubscriberToBroadcasterStatefulMessageType.SUBSCRIBE_EXACT:
    print(message.topic)
```

Serialization:

```python
from lonelypsp.stateful.constants import SubscriberToBroadcasterStatefulMessageType
from lonelypsp.stateful.messages.subscribe import S2B_SubscribeExact, serialize_s2b_subscribe_exact

message = serialize_s2b_subscribe_exact(
    S2B_SubscribeExact(
        type=SubscriberToBroadcasterStatefulMessageType.SUBSCRIBE_EXACT,
        authorization=None,
        topic=b"foo/bar",
    ),
    minimal_headers=True
)
# message: bytearray(b'\x00\x01\x00\x02\x00\x00\x00\x07foo/bar')
```

## Tracing

To facilitate all types of tracing requirements (logging, metrics, debugging, etc),
this protocol supports a tracing header which can be passed along with every message.
The details of how this tracing header is used are up to the broadcaster and subscriber
implementation, but typically the subscriber will send timestamps/ids that are then
stored by the broadcaster, while the broadcaster sends back its own timestamps/ids
for logging on the subscriber side

Tracing data is required to be less than 2^16 bytes and is included in the authorization
checks where relevant (e.g., hmac)
