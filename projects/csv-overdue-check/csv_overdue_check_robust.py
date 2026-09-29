#!/usr/bin/env python3
"""Date-aware CSV overdue check for freelancers and small agencies (robust input).

Forked from agents/x_dev/csv_overdue_check_fixed.py (sha fd7bf358). Stage logic
and original selftests are unchanged. What this version adds:
  - header names are case/space-insensitive, a UTF-8 BOM is tolerated
  - amounts like "$1,200.50" or " 300 " are parsed; empty/garbage amounts are skipped
  - due dates that are not YYYY-MM-DD are skipped (not guessed) and reported
  - blank lines are ignored; skipped rows are listed with their line number
  - a missing required column stops with exit code 2 and a clear message

Usage:
  csv_overdue_check_robust.py --date YYYY-MM-DD [--csv FILE]
  csv_overdue_check_robust.py --selftest

CSV columns (any order, any case): id,client,amount,due

Stage boundaries match late_invoice_reminder.py:
  1-7 Stage 1 First reminder | 8-21 Stage 2 Second reminder
  22-44 Stage 3 Final notice | 45+ Stage 4 Formal demand

Limits: counts days only; does not calculate interest (use late_invoice_reminder.py).
Only ISO dates are accepted on purpose, because 03/04/2026 is ambiguous (US vs UK).
"""
import argparse
import csv
import datetime
import io
import re
import sys

REQUIRED = ("id", "client", "amount", "due")

STAGES = (
    (7, 1, "First reminder"),
    (21, 2, "Second reminder"),
    (44, 3, "Final notice"),
    (float("inf"), 4, "Formal demand"),
)

SAMPLE = (
    "id,client,amount,due\n"
    "INV-101,Acme Studio,1200,2026-09-20\n"
    "INV-102,Northwind,450,2026-08-30\n"
    "INV-103,Blue Fern,3000,2026-08-01\n"
    "INV-104,PaidCo,900,2026-09-10\n"
    "INV-105,GoodClient,2400,2026-12-01\n"
)

MESSY = (
    "\ufeffId , Client ,Amount,Due\n"
    "INV-201,Acme Studio,\"$1,200.50\",2026-09-20\n"
    "INV-202,Northwind,450,09/30/2026\n"
    "INV-203,Blue Fern,,2026-08-01\n"
    "\n"
    "INV-204, Spaced , 300 , 2026-09-01 \n"
)


def stage(days):
    for lim, sid, name in STAGES:
        if days <= lim:
            return sid, name
    return 4, "Formal demand"


def parse_rows(text):
    rdr = csv.reader(io.StringIO(text))
    try:
        first = next(rdr)
    except StopIteration:
        raise ValueError("CSV is empty")
    header = [h.replace("\ufeff", "").strip().lower() for h in first]
    missing = [c for c in REQUIRED if c not in header]
    if missing:
        raise ValueError("missing column(s): " + ", ".join(missing))
    rows = []
    for lineno, raw in enumerate(rdr, start=2):
        if not any(c.strip() for c in raw):
            continue
        d = {header[i]: (raw[i].strip() if i < len(raw) else "") for i in range(len(header))}
        d["_line"] = lineno
        rows.append(d)
    return rows


def parse_amount(s):
    cleaned = re.sub(r"[^0-9.\-]", "", s or "")
    if cleaned in ("", "-", ".", "-."):
        raise ValueError
    return float(cleaned)


def check(rows, asof):
    res, skipped = [], []
    for r in rows:
        line = r.get("_line", 0)
        try:
            due = datetime.date.fromisoformat(r["due"].strip())
        except ValueError:
            skipped.append((line, "due date not YYYY-MM-DD: %r" % r["due"]))
            continue
        try:
            amount = parse_amount(r["amount"])
        except ValueError:
            skipped.append((line, "amount not a number: %r" % r["amount"]))
            continue
        days = (asof - due).days
        if days <= 0:
            continue
        sid, name = stage(days)
        res.append({"id": r["id"], "client": r["client"], "amount": amount,
                    "days": days, "stage": sid, "name": name})
    res.sort(key=lambda x: -x["days"])
    return res, skipped


def emit(res, skipped, out=sys.stdout):
    if not res:
        out.write("No overdue invoices.\n")
    else:
        total = sum(x["amount"] for x in res)
        out.write("%d overdue invoices, total %s\n\n" % (len(res), f"{total:,.2f}"))
        for x in res:
            out.write("%s  %s  %s  %d days  [stage %d %s]\n" % (
                x["id"], x["client"], f"{x['amount']:,.2f}", x["days"], x["stage"], x["name"]))
    if skipped:
        out.write("\nSkipped %d row(s) - please fix and re-run:\n" % len(skipped))
        for line, why in skipped:
            out.write("  line %d: %s\n" % (line, why))


def selftest():
    fails = 0

    def eq(label, want, got):
        nonlocal fails
        if want != got:
            print("FAIL", label, want, got)
            fails += 1

    rows = parse_rows(SAMPLE)
    cases = [
        (datetime.date(2026, 9, 26), ["INV-103", "INV-102", "INV-104", "INV-101"], [56, 27, 16, 6], 5550.00),
        (datetime.date(2026, 9, 25), ["INV-103", "INV-102", "INV-104", "INV-101"], [55, 26, 15, 5], 5550.00),
        (datetime.date(2027, 1, 1), ["INV-103", "INV-102", "INV-104", "INV-101", "INV-105"], [153, 124, 113, 103, 31], 7950.00),
        (datetime.date(2026, 12, 15), ["INV-103", "INV-102", "INV-104", "INV-101", "INV-105"], [136, 107, 96, 86, 14], 7950.00),
    ]
    for asof, ids, days, total in cases:
        res, sk = check(rows, asof)
        tag = asof.isoformat()
        eq("ids " + tag, ids, [x["id"] for x in res])
        eq("days " + tag, days, [x["days"] for x in res])
        eq("total " + tag, total, sum(x["amount"] for x in res))
        eq("skipped " + tag, [], sk)

    # messy input: BOM, spaced headers, $ and commas, bad date, empty amount, blank line
    res, sk = check(parse_rows(MESSY), datetime.date(2026, 9, 26))
    eq("messy ids", ["INV-204", "INV-201"], [x["id"] for x in res])
    eq("messy days", [25, 6], [x["days"] for x in res])
    eq("messy stages", [3, 1], [x["stage"] for x in res])
    eq("messy total", 1500.50, sum(x["amount"] for x in res))
    eq("messy client strip", "Spaced", res[0]["client"] if res else None)
    eq("messy skipped lines", [3, 4], [s[0] for s in sk])

    # missing column must raise
    try:
        parse_rows("id,client,amount\nA,B,1\n")
        eq("missing column raises", True, False)
    except ValueError:
        pass

    if fails == 0:
        print("SELFTEST: ALL PASS (0 fails)")
        return 0
    print(f"SELFTEST: {fails} FAIL")
    return 1


def main():
    if "--selftest" in sys.argv:
        return selftest()
    parser = argparse.ArgumentParser(description="CSV overdue check (robust input)")
    parser.add_argument("--date", required=True, help="reference date YYYY-MM-DD")
    parser.add_argument("--csv", help="path to CSV file; omit to use built-in sample")
    args = parser.parse_args()
    try:
        asof = datetime.date.fromisoformat(args.date)
    except ValueError:
        print("Error: --date must be YYYY-MM-DD")
        return 2
    try:
        if args.csv:
            with open(args.csv, newline="", encoding="utf-8-sig") as fh:
                text = fh.read()
        else:
            text = SAMPLE
        rows = parse_rows(text)
    except FileNotFoundError:
        print(f"Error: file not found: {args.csv}")
        return 2
    except ValueError as e:
        print(f"Error: {e}")
        return 2
    res, skipped = check(rows, asof)
    emit(res, skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
