---
name: payment-followup-skill
description: Use this skill when helping a freelancer write, schedule, or review invoice and late-payment emails, calculate documented USD/GBP late-payment amounts, or build a quote/invoice follow-up tracker.
compatibility: Plain Markdown guidance plus Python 3 standard-library scripts; no network or external account required.
---

# Freelance Payment Follow-Up Skill

Use the evidence-first workflow below. Do not invent rates, payment dates, tax thresholds, collection results, or client promises. Adapt legal and tax wording to the user's jurisdiction.

## 1. Classify the money situation

Choose exactly one:

- Quote not answered
- Invoice within terms
- Overdue, no dispute
- Partial payment
- Invoice disputed
- Never paid
- End-of-project closeout

Do not send a late-payment escalation when the issue is a quote follow-up or a documented dispute. Separate undisputed balance from disputed line items.

## 2. Pick the template

Use this cadence:

| Stage | Timing | Purpose |
|---|---|---|
| Confirmation | invoice sent | State amount, due date, method, contract clause |
| Friendly reminder | due date +3 | Assume an oversight |
| Firm reminder | due date +14 | Restate balance and next step |
| Final notice | due date +30 | Contract clause and one deadline |

If the dispute is open, follow the dispute path first, not the escalation ladder.

## 3. Late-payment calculation

For USD: amount × annual_rate × days / 365, rounded to cents. Default rate is 18%/yr when no contract rate is given.

For GBP: amount × (Bank of England base rate + 8%) × days / 365, plus a fixed compensation fee (<GBP 1000 → £40, 1000..<10000 → £70, >=10000 → £100). Base rate defaults to 5.25%.

These formulas match the team-reviewed `scripts/payment_calculator.py`. Run `python3 scripts/payment_calculator.py --selftest` to reproduce the documented coordinates.

## 4. Quote follow-up tracker

Use `scripts/quote_followup_tracker_demo.csv` as the shape. Columns: quote_id, client, amount, sent_date, follow_up_1, follow_up_2, follow_up_3, status. Follow-ups are scheduled on day 7, 14, 21, 30 after the quote is sent; `closed` means accepted or rejected, `hold` means on pause.

## 5. Evidence and review

Do not publish or credit any claim unless a reviewed output or an actual customer confirmation exists. Do not add links or promises that the skill cannot verify.
