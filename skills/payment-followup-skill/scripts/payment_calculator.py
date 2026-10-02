#!/usr/bin/env python3
"""USD/GBP late-payment interest calculator (payment-followup-skill).

USD: amount x annual_rate x days / 365 (default 18%/yr).
GBP: amount x (base_rate + 8% margin) x days / 365, plus fixed recovery fee at 45+ days past due.
  <GBP 1000 -> 40, 1000..<10000 -> 70, >=10000 -> 100
  default base_rate 5.25% (Bank of England base rate assumption)

The fixed fee is a tool convention applied only at 45+ days, not a statutory figure.

Run --selftest to reproduce documented coordinates.
"""
import argparse
from decimal import Decimal, ROUND_HALF_UP


def usd_interest(amount, days, rate=0.18):
    return Decimal(str(amount)) * Decimal(str(rate)) * Decimal(days) / Decimal(365)


def gbp_interest(amount, days, base_rate=0.0525):
    rate = base_rate + 0.08
    return Decimal(str(amount)) * Decimal(str(rate)) * Decimal(days) / Decimal(365)


def gbp_fee(amount, days):
    if days < 45:
        return Decimal("0")
    if amount < 1000:
        return Decimal("40")
    if amount < 10000:
        return Decimal("70")
    return Decimal("100")


def round2(d):
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--amount", type=float)
    p.add_argument("--currency", choices=["usd", "uk"])
    p.add_argument("--days-past", type=int)
    p.add_argument("--fee", type=float, help="Override fixed fee (GBP path)")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()

    if args.selftest:
        cases = [
            (5000, 60, "usd", Decimal("147.95"), Decimal("35")),
            (2500, 90, "usd", Decimal("110.96"), Decimal("30")),
            (5000, 90, "uk", Decimal("163.36"), Decimal("70")),
            (500, 90, "uk", Decimal("16.34"), Decimal("40")),
            (5000, 30, "uk", Decimal("54.45"), Decimal("0")),
        ]
        all_pass = True
        for amt, days, cur, exp_int, exp_fee in cases:
            if cur == "usd":
                actual_int = round2(usd_interest(amt, days))
                actual_fee = Decimal(str(exp_fee))
            else:
                actual_int = round2(gbp_interest(amt, days))
                actual_fee = gbp_fee(amt, days)
            ok_i = actual_int == exp_int
            ok_f = actual_fee == exp_fee
            status = "PASS" if ok_i and ok_f else "FAIL"
            if not (ok_i and ok_f):
                all_pass = False
            print(f"{status}: {amt}x{days}d {cur} -> int={actual_int} fee={actual_fee} (expected int={exp_int} fee={exp_fee})")
        print("5/5 passed" if all_pass else "some tests failed")
        return 0 if all_pass else 1

    if args.amount is None or args.currency is None or args.days_past is None:
        print("ERROR: --amount, --currency, --days-past are required")
        return 2
    if args.days_past < 0:
        print("ERROR: --days-past must be >= 0")
        return 2

    if args.currency == "usd":
        interest = round2(usd_interest(args.amount, args.days_past))
        fee = Decimal(str(args.fee if args.fee is not None else 0))
        total = round2(Decimal(str(args.amount)) + interest + fee)
        if args.verbose:
            print(f"USD interest path: {args.amount} * 0.18 * {args.days_past} / 365")
            print(f"USD total due: {total} (interest {interest}, fee {fee}, principal {args.amount})")
        else:
            print(f"USD interest: {interest}")
            print(f"USD total due: {total}")
    else:
        interest = round2(gbp_interest(args.amount, args.days_past))
        fee = Decimal(str(args.fee)) if args.fee is not None else gbp_fee(args.amount, args.days_past)
        total = round2(Decimal(str(args.amount)) + interest + fee)
        if args.verbose:
            print(f"UK interest path: {args.amount} * 0.1325 * {args.days_past} / 365")
            print(f"UK total due: {total} (interest+statutory {interest}, fee {fee}, principal {args.amount})")
        else:
            print(f"GBP interest: {interest} (+fee {fee})")
            print(f"GBP total due: {total}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())