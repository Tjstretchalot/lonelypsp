This module doesn't really make sense in this library except that the code is
necessary to implement the desired semantics for both lonelypss and lonelypsc,
which both use lonelypsp, making this a convenient place to put these
utilities.

Alternatively, could duplicate this to both spots or make a utils library and
put that in pypi and depend on it for both, which isn't great, or make a really
specific library for pypi (e.g., "bounded_deque"), which will lead to an excessive
number of projects
