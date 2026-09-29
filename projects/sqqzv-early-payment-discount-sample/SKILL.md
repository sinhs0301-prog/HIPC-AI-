---
name: sqqzv-early-payment-discount-sample
---
# Free worked examples for sizing an early-payment discount

This folder is a free reference sample for the Early Payment Discount Calculator (USD 3, Python script) at https://sinhscribe.gumroad.com/l/sqqzv . It shows the same inputs and outputs you can run in the calculator, so you can check the math before deciding.

## What this folder is
- A free, read-only worked-example sample. It does not replace the calculator and does not send anything.
- Companion to the paid tool: the calculator runs one invoice at a time with the same formula.
- Not financial or legal advice.

## The formula (simple, no compounding)
- discount = invoice amount x (discount rate / 100)
- net payment = invoice amount - discount
- annualized equivalent (context only, not a charge) = discount / invoice amount x 365 / days early x 100
- All money figures are rounded to cents (half-up).

## Worked examples (runnable in the calculator)

Example 1 - $1,000 invoice, 2% discount, 10 days early:
- discount = 1,000 x 2/100 = $20.00
- net payment = $980.00
- annualized equivalent = 20/1000 x 365/10 x 100 = 73.00% (context only)

Example 2 - $3,000 invoice, 1.5% discount, 15 days early:
- discount = 3,000 x 1.5/100 = $45.00
- net payment = $2,955.00
- annualized equivalent = 45/3000 x 365/15 x 100 = 36.50% (context only)

## How to use the paid calculator
- Install Python 3, then: python EARLY_PAYMENT_DISCOUNT.py --amount 1000 --discount_rate 2 --days_early 10
- Run --selftest to check the built-in examples.
- The annualized rate is shown for comparison only; it is not added to the invoice.

## Limits
- One invoice at a time. No email, spreadsheet, or multi-invoice tracking.
- The annualized figure assumes the client would otherwise pay exactly on the due date.
- Review the output and send any message yourself.

## Get the calculator
- Early Payment Discount Calculator for Freelancers (USD 3): https://sinhscribe.gumroad.com/l/sqqzv
