# Freelance Payment Follow-Up Skill

This skill helps a freelancer (or an AI assistant working for one) classify a money situation, pick the right invoice/quote follow-up message, calculate documented late-payment amounts for USD and GBP, and build a quote follow-up tracker.

## What is included

- `SKILL.md` — the workflow, cadence table, and calculation rules.
- `scripts/payment_calculator.py` — computes USD interest (annual rate x days/365) and GBP interest (base rate + 8% margin, plus a fixed recovery fee under 45+ days).
- `scripts/quote_followup.py` — classifies a quote's age into day0/day3/day14/day30 stages and prints a suggested action.

## Install

Copy the `payment-followup-skill` folder into your agent's `skills/` directory. No network access or external account is required. Python 3 standard library only.

## Usage examples

Calculate a USD late amount:

```
python3 scripts/payment_calculator.py --amount 5000 --currency usd --days-past 60 --fee 35 --verbose
```

Check what stage a quote follow-up is in:

```
python3 scripts/quote_followup.py --sent-date 2026-09-14 --today 2026-10-02
```

Run the built-in self-tests:

```
python3 scripts/payment_calculator.py --selftest
python3 scripts/quote_followup.py --selftest
```

## Limitations

- Rates and thresholds (18%/yr USD default, Bank of England base 5.25% + 8% GBP default, fixed fee tiers) are tool conventions, not statutory figures. The UK fixed compensation amounts (£40/£70/£100) are a tool convention, not the 1998 Act's statutory values.
- Legal, tax, and collection wording must be adapted to your jurisdiction and contract. This is not legal advice.
- The quote tracker stages (day0/3/14/30) apply to quotes not yet accepted. Invoice escalation stages (1-7/8-21/22-44/45+) are a separate ladder and should not be mixed with quote follow-ups.

## License

MIT — see LICENSE.

Made by a small AI team.
