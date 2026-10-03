import dns.exception
import dns.resolver
import pytest

from bot.services.email_domains import EmailDomainChecker


class _MX:
    def __init__(self, exchange: str) -> None:
        self.exchange = dns.name.from_text(exchange)


class FakeResolver:
    def __init__(self, answers: dict[str, list[str] | Exception]) -> None:
        self.answers = answers
        self.calls: list[str] = []

    async def resolve(self, domain: str, rdtype: str, lifetime: float):
        assert rdtype == "MX"
        self.calls.append(domain)
        answer = self.answers[domain]
        if isinstance(answer, Exception):
            raise answer
        return [_MX(exchange) for exchange in answer]


def make_checker(answers) -> tuple[EmailDomainChecker, FakeResolver]:
    checker = EmailDomainChecker()
    resolver = FakeResolver(answers)
    checker._resolver = resolver  # type: ignore[assignment]
    return checker, resolver


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        (["mx1.inbox.lv.", "mx2.inbox.lv."], True),
        (["."], False),  # null MX: the domain says it takes no mail (gmail.co, example.com)
        (dns.resolver.NXDOMAIN(), False),  # the domain doesn't exist
        (dns.resolver.NoAnswer(), False),  # exists, but has no mail servers
        (dns.exception.Timeout(), True),  # DNS trouble must not block the order
        (dns.resolver.NoNameservers(), True),
    ],
)
async def test_accepts_mail(answer, expected):
    checker, _ = make_checker({"x.lv": answer})
    assert await checker.accepts_mail("x.lv") is expected


async def test_definite_answers_are_cached_failures_are_not():
    checker, resolver = make_checker({"good.lv": ["mx.good.lv."], "slow.lv": dns.exception.Timeout()})
    for _ in range(2):
        assert await checker.accepts_mail("good.lv")
        assert await checker.accepts_mail("slow.lv")
    assert resolver.calls == ["good.lv", "slow.lv", "slow.lv"]
