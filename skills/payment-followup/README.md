# Payment Follow-Up Skill

A lightweight skill for freelancers who need help with invoice follow-ups, late-payment notices, and quote tracking.

## Install

Place the entire `payment-followup/` folder under your agent skills directory (`skills/payment-followup/` or your local equivalent). No external services or network calls are needed.

## Requirements

- Any AI agent that can load plain Markdown instructions
- Python 3 standard library for optional calculation helpers
- No external account, API key, or paid service

## Usage

- Ask the agent to use this skill when you need to write, schedule, or review invoice and late-payment emails
- Ask for a quote/invoice follow-up tracker when tracking sent quotes and scheduled follow-ups
- Ask for documented USD or GBP late-payment calculations when applying a rate you already have in writing

## Examples

1. "My invoice is 14 days overdue and not disputed. Draft a firm reminder." (Stage 2 of the cadence)
2. "Write a final notice for an invoice 30 days past due, referencing the contract clause." (Stage 3)
3. "What should I do first if a client has never paid any invoice on this project?" (Never-paid path, see SKILL.md section 1)
4. "Build a quote follow-up tracker that schedules reminders on days 7/14/21/30." (See the tracker CSV template and the documented cadence)

## Limitations

- Not legal or tax advice; adapt wording and terms to your own contract and local rules
- Amounts, due dates, tax thresholds, and collection outcomes must come from your records — the skill never invents them
- Late-payment calculations apply only rates you state in writing; no contract rate means the documented tools report interest of 0.00

## License

MIT