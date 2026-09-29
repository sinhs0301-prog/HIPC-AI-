---
name: uk-late-payment-interest-sample
description: Free sample skill. Helps an agent work out UK statutory late payment interest and fixed compensation on an overdue B2B invoice, and draft a short, factual claim line. Use when a UK-based supplier asks how much they can add to an unpaid business invoice.
---

# UK Late Payment Interest (free sample)

This is a free sample. It gives the method and one worked example. It is not legal or tax advice.

## When to use
- The invoice is business-to-business (not a consumer sale).
- The contract does not set its own late payment interest rate. If it does, the contract rate applies instead of the statutory one.
- The user can give: invoice amount (GBP), due date, the date to calculate to, and the Bank of England base rate for the relevant six-month period.

## Steps
1. Ask for the four inputs above. Do not guess the base rate. The reference rate is the base rate on 31 December (for invoices falling due January to June) or 30 June (for July to December). Ask the user to confirm it.
2. Days overdue = calculation date minus due date. If this is 0 or negative, stop and say the invoice is not overdue yet.
3. Statutory rate = base rate + 8 percentage points.
4. Interest = amount x (statutory rate / 100) x days / 365. Round the final figure once, half up, to the penny.
5. Fixed compensation, once per invoice:
   - under GBP 1,000: GBP 40
   - GBP 1,000 to GBP 9,999.99: GBP 70
   - GBP 10,000 or more: GBP 100
6. Total claim = amount + interest + compensation.
7. Show the working line by line so the user can check it.

## Worked example
Invoice GBP 1,000.00, base rate 4%, 30 days overdue.
- Rate = 4 + 8 = 12%
- Interest = 1000 x 0.12 x 30 / 365 = 9.863... -> GBP 9.86
- Compensation = GBP 70 (amount is GBP 1,000 or more)
- Total = GBP 1,079.86

## Claim line template
"Invoice [number] for GBP [amount] was due on [date] and is [days] days overdue. Under the Late Payment of Commercial Debts (Interest) Act 1998, statutory interest of GBP [interest] ([rate]% a year) and fixed compensation of GBP [compensation] now apply. The total due is GBP [total]."

## Limits
- Simple interest only; no compounding.
- Does not handle part payments, disputed invoices, or contract-specific rates.
- Check the current rules on the official UK government guidance before sending a claim.

## Paid version
A Python calculator that does these steps from the command line, with a built-in self-test covering the GBP 40/70/100 boundaries, is sold separately (USD 3): https://sinhscribe.gumroad.com/l/nlansn
