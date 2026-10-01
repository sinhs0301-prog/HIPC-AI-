---
name: payment-followup
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

If the dispute is open, follow the dispute path instead of the dunning path; the undisputed portion still gets a dated reminder but never mixes tone with the disputed line.

## 3. Calculate late fees only when the contract says so

- USD: daily interest on a 365-day year; no interest or fixed fee before 45 days past invoice date unless the contract names it.
- GBP: statutory fixed compensation under the Late Payment of Commercial Debts (Interest) Act 1998: £40 under £1,000; £70 £1,000 to £10,000; £100 £10,000 and above.

Run the included scripts for the exact numbers and do not restate a figure the script does not produce.

## 4. Build the tracker

The CSV template columns are:

quote_id, client, amount, sent_date, follow_up_1, follow_up_2, follow_up_3, status

- follow_up dates are sent_date + 7, + 14, + 21 calendar days.
- status is one of pending, closed, declined, hold.

## 5. Verify before publishing or sending

Check the three facts that make the letter defensible:

1. the unpaid balance, including interest only if the contract states it
2. the exact clause and the invoice date
3. a final deadline and one consequence

A letter that names the clause is a notice; a letter that threatens is an argument.

## License

MIT. Created by the HIPC-AI products team; verify platform rules and local law before commercial use.
