"""Checks that an e-mail domain really exists and accepts mail, via a DNS MX lookup.

Any real domain passes (gmail.com, inbox.lv, edu.riga.lv, a company domain); made-up or mistyped ones
fail: gmail.co and example.com publish a "null MX" (RFC 7505) saying they take no mail, and
inbox.lvv simply doesn't exist. If DNS itself is down or slow the address is accepted, so a resolver
outage never blocks an order.
"""

from __future__ import annotations

import logging
import time

import dns.asyncresolver
import dns.exception
import dns.name
import dns.resolver

logger = logging.getLogger(__name__)

# Answers that prove the domain can't receive mail (as opposed to "DNS didn't answer").
_NO_MAIL = (
    dns.resolver.NXDOMAIN,
    dns.resolver.NoAnswer,
    dns.name.IDNAException,
    dns.name.LabelTooLong,
    dns.name.NameTooLong,
)


class EmailDomainChecker:
    def __init__(self, timeout: float = 5.0, cache_ttl: float = 3600, cache_size: int = 1024) -> None:
        self._timeout = timeout
        self._cache_ttl = cache_ttl
        self._cache_size = cache_size
        self._cache: dict[str, tuple[float, bool]] = {}
        self._resolver: dns.asyncresolver.Resolver | None = None

    async def accepts_mail(self, domain: str) -> bool:
        cached = self._cache.get(domain)
        if cached and cached[0] > time.monotonic():
            return cached[1]
        result = await self._lookup(domain)
        if result is None:
            return True  # DNS trouble: let the user through and don't remember the guess
        if len(self._cache) >= self._cache_size:
            self._cache.clear()
        self._cache[domain] = (time.monotonic() + self._cache_ttl, result)
        return result

    async def _lookup(self, domain: str) -> bool | None:
        try:
            if self._resolver is None:
                self._resolver = dns.asyncresolver.Resolver()  # reads the system resolver config
            answer = await self._resolver.resolve(domain, "MX", lifetime=self._timeout)
        except _NO_MAIL:
            return False
        except dns.exception.DNSException as exc:
            logger.warning("MX lookup for %s failed (%r); accepting the address", domain, exc)
            return None
        return any(record.exchange.to_text() != "." for record in answer)
