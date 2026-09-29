# uk-late-payment-interest-sample

A free sample agent skill that helps an AI assistant explain and calculate **UK statutory interest and fixed compensation on late B2B invoices**. It is based on the Late Payment of Commercial Debts (Interest) Act 1998.

This is general information, not legal advice. Check your own contract and current rates before you send any claim.

## What is in this folder

- `SKILL.md`: the instructions the agent follows (inputs to ask for, formula, compensation bands, output format, limits)
- `README.md`: this file
- `LICENSE`: terms of use for this free sample

## Install

1. Copy the whole folder `uk-late-payment-interest-sample/` into your agent's skills directory. For Claude Code this is usually `~/.claude/skills/` (per user) or `.claude/skills/` inside a project.
2. Keep the folder name unchanged, because it must match the `name` field in `SKILL.md`.
3. Restart or reload the agent so it picks up the new skill.

## Usage example

Ask the agent something like:

> A UK business client owes me GBP 1,000. The invoice is 30 days overdue. Assume the Bank of England base rate was 4% on the reference date. What can I claim?

The expected calculation:

- Statutory rate = 8% + 4% base rate = 12% per year
- Interest = 1,000 x 0.12 x 30 / 365 = GBP 9.86
- Fixed compensation for a debt of GBP 1,000 to 9,999.99 = GBP 70
- Total claim = 1,000 + 9.86 + 70 = GBP 1,079.86

Fixed compensation bands: under GBP 1,000 = GBP 40; GBP 1,000 to 9,999.99 = GBP 70; GBP 10,000 or more = GBP 100.

## Limits

- Applies to business-to-business debts only, not consumer sales.
- The base rate used is the one in force on the reference date (31 December for debts falling due January to June, 30 June for debts falling due July to December). The agent does not look it up; you must supply it.
- A contract that sets its own substantial remedy for late payment can replace the statutory rate.
- Simple (not compound) interest, calculated per day on a 365-day year.

## Relation to paid products

This sample is free. The team also sells separate paid calculators on Gumroad (store: sinhscribe). Nothing in this free sample is sold there, and this sample must not be resold.
