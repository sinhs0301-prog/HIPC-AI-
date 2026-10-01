#!/usr/bin/env python3
"""Late-payment calculator for the payment-followup skill (USD and GBP).

Formulas verified against the team-reviewed duo_fixed.py and calculator runs
(95283e03, c4cd31ca, c133d171, 6c732b3c, de8bb817, 2e778e08):
- USD: amount * annual_rate * days / 365, rounded to cents (ROUND_HALF_UP).
  Default rate 18%/yr. Example: $2,000 at 18% for 30 days = 29.59.
- UK: amount * (Bank of England base rate + 8%) * days / 365, plus a fixed
  statutory compensation fee (<GBP 1000 -> 40, 1000..<10000 -> 70,
  >=10000 -> 100). Base rate defaults to 5.25, so the rate is 13.25%.

Run --selftest with no other arguments to check documented examples.
"""

import sys
from decimal import Decimal, ROUND_HALF_UP


def q(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def usd_late(amount, days, rate=Decimal("0.18")):
    """USD simple interest: amount * rate * days / 365."""
    return q(Decimal(amount) * Decimal(rate) * Decimal(days) / Decimal(365))


def uk_late(amount, days, base_rate=Decimal("5.25")):
    """UK statutory: amount * (base_rate+8)% * days/365 + fixed fee."""
    interest = q(
        Decimal(amount)
        * (Decimal(base_rate) / Decimal(100) + Decimal(8) / Decimal(100))
        * Decimal(days)
        / Decimal(365)
    )
    a = Decimal(amount)
    if a < Decimal("1000"):
        fee = Decimal("40")
    elif a < Decimal("10000"):
        fee = Decimal("70")
    else:
        fee = Decimal("100")
    return q(interest + fee)


def selftest():
    ok = True

    def check(label, got, exp):
        nonlocal ok
        if got == exp:
            print("PASS: %s -> %s (expected %s)" % (label, got, exp))
        else:
            ok = False
            print("FAIL: %s -> %s (expected %s)" % (label, got, exp))

    check("usd 2000/22d", usd_late(2000, 22), Decimal("21.70"))
    check("usd 1000/22d", usd_late(1000, 22), Decimal("10.85"))
    check("usd 1500/22d", usd_late(1500, 22), Decimal("16.27"))
    check("usd 2000/30d", usd_late(2000, 30), Decimal("29.59"))
    check("uk 500/5d", uk_late(500, 5), Decimal("40.91"))
    check("uk 1000/5d", uk_late(1000, 5), Decimal("71.82"))
    check("uk 10000/5d", uk_late(10000, 5), Decimal("118.15"))

    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(selftest())
    print("usage: payment_calculator.py --selftest")
    sys.exit(2)
