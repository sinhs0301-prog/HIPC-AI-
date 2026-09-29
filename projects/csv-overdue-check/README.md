# csv-overdue-check

A small, dependency-free Python script that reads a CSV of unpaid invoices and tells you which ones are overdue on a given date, how many days late each one is, and which follow-up stage it falls into.

It only counts days. It does not send email, calculate interest, or give legal advice.

## Requirements

- Python 3.7 or newer (standard library only)

## Usage

```
python csv_overdue_check_robust.py --date 2026-09-29 --csv invoices.csv
python csv_overdue_check_robust.py --date 2026-09-29          # uses the built-in sample
python csv_overdue_check_robust.py --selftest
```

## CSV format

Four columns, in any order, any letter case: `id,client,amount,due`

```
id,client,amount,due
INV-101,Acme Studio,1200,2026-09-20
INV-102,Northwind,450,2026-08-30
```

- `due` must be `YYYY-MM-DD`. Other formats such as `09/30/2026` are skipped and reported, not guessed, because `03/04/2026` means different dates in the US and the UK.
- `amount` may contain `$` and thousands separators (`"$1,200.50"`). Rows with an empty or non-numeric amount are skipped and reported.
- A UTF-8 BOM, spaces around headers and values, and blank lines are tolerated.
- If a required column is missing, the script stops with exit code 2 and names the missing column.

## Output

Overdue invoices are listed from most to least overdue, with a total:

```
4 overdue invoices, total 5,550.00

INV-103  Blue Fern  3,000.00  56 days  [stage 4 Formal demand]
...
```

Skipped rows are listed at the end with their line number and the reason.

## Stages

| Days overdue | Stage |
|---|---|
| 1-7 | 1 First reminder |
| 8-21 | 2 Second reminder |
| 22-44 | 3 Final notice |
| 45+ | 4 Formal demand |

The stage names are labels for planning your follow-up. They are not legal categories.

## Testing

`--selftest` checks the built-in sample on four dates and a deliberately messy CSV (BOM, spaced headers, `$` amounts, a non-ISO date, an empty amount, a blank line) plus the missing-column error. It prints `SELFTEST: ALL PASS (0 fails)` when everything matches.

## Limits

- Not yet tested against real exported CSVs from specific invoicing tools; you may need to rename your columns to `id,client,amount,due`.
- No currency handling: amounts are summed as plain numbers.
- No interest or late-fee calculation.

## Related paid tool (optional)

If you also want stage-matched reminder email text and a late-fee/interest calculation, the same team sells a separate script on Gumroad: https://sinhscribe.gumroad.com. This free checker works on its own without it.

## License and authorship

Written by an AI team (Hermes lab) for the repository owner. Free to use, modify, and redistribute. Provided as is, without warranty.
