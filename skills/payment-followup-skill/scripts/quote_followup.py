#!/usr/bin/env python3
"""Quote follow-up stage classifier (payment-followup-skill).

day0  <3 days elapsed
day3  3-13
day14 14-29
day30 30+

Run --selftest to reproduce the 4-stage classification.
"""
import argparse
from datetime import date, timedelta


def classify(days):
    if days < 3:
        return "day0", "Quote just sent. Confirm receipt, ask if they need anything else."
    if days < 14:
        return "day3", "Friendly check-in. Ask if the quote reached the right person."
    if days < 30:
        return "day14", "Direct follow-up. Ask for a decision or a specific date to discuss."
    return "day30", "Final follow-up. State that you will close the quote if you do not hear back."


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sent-date")
    p.add_argument("--today")
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()
    if args.selftest:
        cases = [(0, "day0"), (3, "day3"), (14, "day14"), (30, "day30")]
        ok = True
        for d, exp in cases:
            got = classify(d)[0]
            status = "PASS" if got == exp else "FAIL"
            if got != exp:
                ok = False
            print(f"{status}: {d}d -> {got} (expected {exp})")
        print("4/4 passed" if ok else "some tests failed")
        return 0 if ok else 1
    sd = date.fromisoformat(args.sent_date)
    today = date.fromisoformat(args.today) if args.today else sd + timedelta(days=30)
    days = (today - sd).days
    if days < 0:
        print("ERROR: sent date is after today")
        return 2
    stage, msg = classify(days)
    print(f"Quote sent: {sd.isoformat()}")
    print(f"Today: {today.isoformat()}")
    print(f"Elapsed: {days} days (stage: {stage})")
    print(f"Suggested action: {msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
