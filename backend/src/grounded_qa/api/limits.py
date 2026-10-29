########################################################################
#                backend/src/grounded_qa/api/limits.py                 #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-10-29

Limits how often one client may ask, so one caller cannot spend the
whole model budget. It keeps recent request times in memory, per
client address, so it holds for one server process. Behind a proxy or
with several workers, the limit belongs in the proxy or a shared store
instead; the README lists this under unresolved questions.
"""

########################################################################
#                               Imports                                #
########################################################################
# Standard library
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

# Third-party
from kds.args import required
from kds.logs import get_logger

########################################################################
#                           Global constants                           #
########################################################################
log = get_logger(__name__)

########################################################################
#                           Local constants                            #
########################################################################
# log.debug("Sets the window the limit counts over, in seconds")
WINDOW_S = 60.0


########################################################################
#                              Rate limit                              #
########################################################################
# log.debug("Defines the limiter")
class RateLimiter:
    """At most `limit` requests per client in any rolling window."""

    # log.debug("Defines the constructor")
    def __init__(
        self,
        limit: int | None = None,
        window_s: float = WINDOW_S,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Builds a limiter of `limit` requests per client per window.

        Args:
            limit: The most requests one client may make in a window.
                Required.
            window_s: The window's length, in seconds.
            clock: The clock request times are read from; tests pass
                their own.
        """
        # log.debug("Takes the limit, which the caller must give")
        limit = required(limit=limit)
        # log.debug("Keeps the limit")
        self.limit = limit
        # log.debug("Keeps the window length")
        self.window_s = window_s
        # log.debug("Keeps the clock, which tests replace")
        self.clock = clock
        # log.debug("Starts each client's list of recent request times")
        self._seen: defaultdict[str, deque[float]] = defaultdict(deque)
        # log.debug("Creates the lock that guards those lists")
        self._lock = threading.Lock()

    # log.debug("Defines the check for one request")
    def allow(self, client: str | None = None) -> bool:
        """Records a request, or refuses it when the client is over.

        Args:
            client: The client's address. Required.

        Returns:
            True when the request was allowed and recorded, False when
            the client has used up the window.
        """
        # log.debug("Takes the client, which the caller must give")
        client = required(client=client)
        # log.debug("Reads the time now")
        now = self.clock()
        # log.debug("Updates the client's list under the lock")
        with self._lock:
            # log.debug("Takes the client's recent request times")
            seen = self._seen[client]
            # log.debug("Forgets requests older than the window")
            while seen and now - seen[0] >= self.window_s:
                # log.debug("Drops the oldest request time")
                seen.popleft()
            # log.debug("Refuses the request when the window is full")
            if len(seen) >= self.limit:
                # log.debug("Returns refused")
                return False
            # log.debug("Records this request")
            seen.append(now)
        # log.debug("Returns allowed")
        return True
