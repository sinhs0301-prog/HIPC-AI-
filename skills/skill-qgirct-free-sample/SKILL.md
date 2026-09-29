---
name: skill-qgirct-free-sample
title: "Free sample: what a 4-stage overdue-invoice reminder looks like"
description: "A free worked example of the 4-stage overdue invoice reminder emails, with a 15-day and 30-day late interest calculation. Free sample of the paid tool qgirct."
metadata:
  idea_key: qgirct_free_sample_skill
  license: MIT
---

# Free sample: what a 4-stage overdue-invoice reminder looks like

A short worked example of the reminder emails our overdue-invoice tool generates. This file is a free sample. The full tool is at https://sinhscribe.gumroad.com/l/qgirct (USD 3). It is not legal or tax advice.

## What the tool does

- You enter the client name, invoice number, amount, due date, and today's date.
- It prints one reminder email and a short calculation block under it.
- It does not send any email, read your inbox, or save any personal data. You copy the text and send it yourself.

## The four stages

| Days past due | Stage | What the email asks for |
|---|---|---|
| 1-7 | 1 friendly check | the original amount only |
| 8-21 | 2 firm reminder | the original amount only |
| 22-44 | 3 formal notice | the original amount plus late interest |
| 45+ | 4 final notice | the original amount plus late interest |

Late interest uses actual days / 365 at the annual rate you enter. If your contract uses a monthly rate, divide by 12 to get the annual figure.

## Worked example (one invoice of USD 1,000, 18% annual rate)

| Days late | Stage | Interest asked for | Calculation |
|-----------|-------|--------------------|-------------|
| 15 | 2 | USD 0.00 (original amount only) | reference: 1,000 x 0.18 x 15 / 365 = USD 7.40 |
| 30 | 3 | USD 14.79 added to the original amount | 1,000 x 0.18 x 30 / 365 = USD 14.79 |

The email at stage 2 asks for the original amount only. The interest figure first appears as a calculation line, and the amount asked for changes only from stage 3.

## Limits

- This is a sample document. It does not send email, connect to any account, or store data.
- Numbers are worked examples verified by running our own script. Results for your own invoices depend on the dates and rate you enter.
- Not legal or tax advice. Check your contract and local rules before charging late interest.
