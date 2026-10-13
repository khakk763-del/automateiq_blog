---
title: Weekly Sales Reports on Autopilot: An n8n Tutorial
description: Build an automated weekly sales report in n8n: pull CRM data, compute KPIs, format a digest, and deliver it to email or Slack on schedule. Beginner-friendly walkthrough.
date: 2026-10-13
slug: automated-weekly-sales-reports-n8n
category: Tutorials
---

# Weekly Sales Reports on Autopilot: An n8n Tutorial

Somebody on your team spends part of every Monday morning building the weekly sales report. They open the CRM, export data, paste it into a spreadsheet, compute the numbers, format an email, and send it. It takes thirty to ninety minutes, it is boring, and the numbers are sometimes wrong because a tired human did arithmetic at 9 a.m.

This tutorial shows you how to build that report once in n8n and never build it manually again. By the end, you will have a workflow that runs on a schedule, pulls data from your CRM or Google Sheets, computes the key numbers, formats a readable digest, and delivers it to email or Slack. Every step is explained in plain language, and I assume you have never built an n8n workflow before.

## What You Need Before You Start

- **An n8n instance.** Either n8n Cloud (hosted, subscription) or a self-hosted install (the core is open-source and free to run yourself). Any recent version works for this tutorial.
- **A data source with your sales data.** This tutorial covers two options: a CRM (I will use HubSpot as the example, but the pattern works for Pipedrive, Salesforce, and others) or a Google Sheets spreadsheet where you track deals. Pick whichever one holds your real data.
- **A delivery channel.** An email address that can receive the report, or a Slack workspace where you can post it. Both are covered.
- **About two hours** for the first build, including testing. Future reports like this will take a fraction of that time because you will reuse the pattern.

You do not need to know JavaScript for the basic version. I will point out exactly where a tiny bit of code becomes useful, and give you the snippets to paste.

## Step 1: Define What the Report Contains

Before touching n8n, decide what numbers actually matter. A report that includes everything is a report nobody reads. For a weekly sales digest, these five KPIs cover most small businesses:

1. **New leads this week** — count of contacts or leads created in the last 7 days.
2. **Conversion rate** — deals won divided by total deals closed (won plus lost) this week. If your cycle is longer than a week, compute it over the trailing 4 weeks instead; a weekly conversion rate on long cycles is noise.
3. **Pipeline value** — sum of deal amounts currently in open stages, plus how it changed versus last week.
4. **Follow-up SLA compliance** — percentage of new leads contacted within your target response time (for example, 1 hour or same business day). This requires a "first contacted" timestamp, which most CRMs can provide.
5. **Stale deals** — count of open deals with no activity in your defined stale period (see our CRM hygiene guide for setting thresholds).

Write these five down with your exact definitions. "Conversion rate" means ten different things to ten different teams; your workflow needs your definition. This ten-minute exercise prevents most of the confusion later.

## Step 2: Connect Your Data Source

### Option A: HubSpot (or another CRM)

In n8n, create a new workflow and add your first node after the trigger (we will add the trigger in Step 3 — n8n lets you build in any order, or start with a manual trigger for testing).

Add a **HubSpot node** and create credentials: in n8n, open the node's credentials dropdown, choose "Create new," and follow the OAuth flow to connect your HubSpot account. n8n handles the OAuth dance; you just log in to HubSpot and approve.

Configure the node to **get all deals**, with filters for what you need. You will actually need a few data pulls:

- Deals created in the last 7 days (for new pipeline and activity).
- All open deals (for pipeline value).
- Deals closed in the reporting window (for conversion rate).
- Contacts created in the last 7 days (for new leads).
- Optionally, engagements or activities for the follow-up SLA calculation.

Do not try to get everything in one giant pull. Separate, focused queries are easier to debug and easier to understand when you revisit the workflow in six months.

### Option B: Google Sheets

If your sales data lives in a spreadsheet, add a **Google Sheets node** instead. Connect via OAuth the same way, then configure it to read the range containing your deals table.

One important discipline for the Sheets version: your sheet needs consistent columns — one row per deal, with columns like Deal Name, Stage, Amount, Created Date, Close Date, Owner, and Last Activity Date. If your sheet is currently a freeform collection of notes, spend twenty minutes normalizing it before building the workflow. Automation cannot fix a spreadsheet with three different date formats in the same column. (It can, actually, with enough code — but you do not want to maintain that.)

## Step 3: Add the Schedule Trigger

Replace your manual test trigger with a **Schedule Trigger node**. Configure it to run weekly — Monday at 7:00 a.m. in your timezone is the classic choice, so the report is waiting when the team arrives.

Two practical notes:

- **Timezone matters.** n8n schedule triggers run in the timezone you configure. If your team spans timezones, pick the one where decisions get made, and say so in the report ("Week of Oct 13, times in Eastern").
- **Keep the manual trigger node** in the workflow but disconnected, or use n8n's "execute workflow" test button. You will want to test-run this workflow many times before Monday morning arrives.

## Step 4: Compute the KPIs

This is the heart of the workflow. You have raw data; now you turn it into numbers. In n8n, the natural tool is the **Code node** (JavaScript), placed after your data pulls. If you have never written JavaScript, do not panic — the logic below is simple arithmetic, and I will give you the pattern.

The Code node receives the items from the previous node as an array. Your job is to loop through them and compute each KPI. Here is the logic in plain language, which you can translate directly:

**New leads:** filter contacts where the created date is within the last 7 days, then count them.

**Pipeline value:** filter deals where the stage is any open stage, then sum the amounts. Also compute last week's pipeline value the same way from a stored snapshot (see Step 6) so you can show the change.

**Conversion rate:** filter deals closed in the window into won and lost, then divide won by (won + lost). Guard against division by zero — if nothing closed this week, report "no closed deals" instead of a percentage.

**Follow-up SLA:** for each new lead, find the time of first contact (first logged call, email, or meeting). Count how many were contacted within your target window, divide by total new leads. If your CRM does not reliably track first-contact time, this KPI will be approximate — say so in the report rather than presenting a false precision.

**Stale deals:** filter open deals where the last activity date is older than your threshold, then count them. Include the top five by value so the team knows which ones hurt most.

Write each computation as a small, separate block with a comment explaining what it does. Future you will be grateful. The Code node then outputs a single JSON object with all five KPIs plus metadata (report date, data source, record counts). That single object becomes the input for the formatting step.

If JavaScript truly is not your thing, you can approximate much of this with n8n's **IF**, **Filter**, and **Aggregate** nodes chained together. It takes more nodes and more clicking, but it works and it is fully visual. There is no shame in the visual route — choose the one you will actually maintain.

## Step 5: Format the Digest

Raw numbers in an email look like a system log. Take five minutes to format them into something a human wants to read. Add an **HTML or Markdown formatting step** — another Code node, or n8n's built-in templating — that turns your KPI object into a digest.

A structure that works well:

- **Headline line:** "Weekly Sales Report — Week of October 13" with the data window stated explicitly.
- **KPI section:** each metric on its own line with the number large, the label clear, and the week-over-week change shown with an up/down indicator and the word "up" or "down" (never rely on color alone — some people read email in plain text).
- **Highlights:** one or two auto-generated observations. You can generate these with simple rules: if conversion rate dropped more than 5 points, add "Conversion dipped this week — X deals lost, worth reviewing." If stale deals grew, say so. Rule-based observations are honest and useful; do not ask an AI to invent narrative insights unless a human reviews them.
- **Action list:** the top 5 stale deals by value with owner names and links to the CRM records. This turns the report from information into assignments.
- **Footer:** data source, generation time, and a one-line note on definitions ("Conversion = won / (won + lost) on deals closed this week").

For Slack delivery, keep the same content but shorter: KPIs as a compact list, and put the stale-deal action list in a threaded reply or a linked document if it gets long. For email, a simple styled HTML template is fine — you do not need a designer, just clean headings and spacing.

## Step 6: Store a Snapshot for Week-over-Week Comparison

A report without history is just a number. To show trends, your workflow needs to remember last week's values. The simplest approach: at the end of each run, write the KPI object to a small store.

Options, easiest first:

- **Append a row to a Google Sheet** acting as your KPI history log: date plus the five numbers. Next week's run reads the last row for comparison. Simple, visible, and easy to audit.
- **Write to a database** (Postgres, MySQL, or even SQLite on a self-hosted instance) if you already run one.
- **Use n8n's static data** (available in the Code node) for lightweight persistence. It works but is harder to inspect than a sheet, so prefer the sheet for your first version.

This step is what transforms the report from "here are numbers" to "here is what changed and whether it is good or bad." Do not skip it.

## Step 7: Deliver It

Add your delivery node at the end:

- **Email:** use the **Gmail**, **Outlook**, or **SMTP** node. Send to the sales team distribution list. Set a clear subject line with the date: "Weekly Sales Report — Oct 13". Send the HTML version as the body.
- **Slack:** use the **Slack node** to post to a channel like #sales. Tag the sales manager only if there is something requiring attention (for example, stale deals above a threshold) — a report that pings everyone every week trains people to mute the channel.

Consider sending to both: email for the record, Slack for visibility. The workflow can branch and do both from the same formatted content.

## Step 8: Error Handling (Do Not Skip This)

A workflow that fails silently is worse than no workflow, because the team assumes the report ran. Build in three safety nets:

1. **Node-level error handling.** In n8n, configure the workflow's error behavior: on failure, route to an error branch that sends you (the owner) a message with what failed. The **Error Trigger** workflow type exists exactly for this — a separate small workflow that fires whenever your report workflow errors, posting the error details to you in Slack or email.
2. **Data sanity checks.** Before formatting, add a quick validation: if the deal pull returned zero records, something is probably wrong with the query or the credentials — halt and alert rather than sending a report full of zeros. A "0 new leads, $0 pipeline" email destroys trust in the automation instantly.
3. **A heartbeat check.** If your team expects the report every Monday at 7, add a dead-man's-switch: a separate scheduled check (or an external uptime monitor hitting an n8n webhook) that alerts you if the report workflow did not complete by 7:30. This catches the case where the whole n8n instance is down.

Test each failure mode deliberately: revoke and restore credentials, point a query at a bad filter, disconnect the network briefly. Watching your error handling work in testing is the only way to trust it on a Monday morning.

## Step 9: Test Like a Skeptic

Before the first scheduled run, test thoroughly:

- **Run with the manual trigger** and inspect every node's output. n8n shows you exactly what data each node produced — click through and verify the numbers against your CRM manually for one week.
- **Check edge cases:** a week with zero new leads, a week with zero closed deals, a deal with a missing amount, a contact with no activity. Your Code node should handle all of these without crashing or producing nonsense.
- **Verify the schedule** by setting it to run once in the next few minutes as a dry run, confirming delivery, then switching to the real weekly schedule.
- **Have a colleague sanity-check the first real report** against numbers they know. If the report says 12 new leads and the CRM shows 12, you are in business.

Keep a testing checklist in the workflow's notes (n8n lets you add sticky notes to the canvas — use them). Six months from now, when you modify the workflow, that checklist is gold.

## Step 10: Maintain It

A reporting workflow is a living thing. Put a quarterly 30-minute review on your calendar:

- Confirm the KPIs still match how the business thinks. Definitions drift; update the workflow when they do.
- Check that pipeline stages in the workflow match the CRM — a renamed stage silently breaks filters.
- Review the error log for the quarter. Recurring warnings are bugs asking to be fixed.
- Rotate credentials if your security policy requires it, and confirm the OAuth connections are still authorized.

That is the entire maintenance burden for most teams: thirty minutes, four times a year.

## Troubleshooting Common Problems

- **"The numbers don't match the CRM."** Almost always a filter mismatch: date ranges, timezones, or stage names. Compare one specific record the workflow counted against the CRM and find where the logic diverges.
- **"The workflow times out."** You are probably pulling too much data. Narrow your queries with date filters and fetch only the fields you need instead of full records.
- **"OAuth keeps disconnecting."** Some CRM OAuth tokens expire if unused or if the connecting user's permissions change. Reconnect, and consider using a dedicated integration user rather than someone's personal account.
- **"Slack shows raw HTML."** You sent the email-formatted version to Slack. Branch the formatting: HTML for email, plain Markdown for Slack.
- **"It worked for weeks, then broke."** Something upstream changed — a renamed pipeline stage, a new required field, an API update. Check the error log first; it usually tells you exactly which node failed and why.

## Frequently Asked Questions

### Do I need to know how to code to build this?

No. The core workflow — trigger, data pull, formatting, delivery — is entirely visual in n8n. JavaScript in a Code node makes the KPI math more compact, but you can build equivalent logic with Filter, IF, and Aggregate nodes. Start visual; add code only where it clearly simplifies things.

### How much does this cost to run?

If you self-host n8n, the workflow itself costs nothing beyond your server, and a weekly report is trivial load. On n8n Cloud or with Zapier/Make, a weekly report consumes a tiny number of executions — this is one of the cheapest automations you can run on any platform. The real cost is the two hours of setup, which pays for itself the first month.

### My data is messy. Should I clean it first or automate first?

Clean the critical fields first — at minimum, consistent date formats and stage names. The workflow in this tutorial includes sanity checks, but automation multiplies whatever quality your data has, good or bad. Our CRM hygiene guide covers the cleanup side if you need it.

### Can I do this in Zapier or Make instead of n8n?

Yes. The architecture is identical: schedule trigger, data pull, compute, format, deliver. Zapier's Paths and Make's routers handle the branching; their built-in formatters and code steps handle the math. n8n's advantages here are cost at scale and the flexibility of the Code node. Choose the tool your team will maintain.

### How do I add more KPIs later?

Add the data pull if needed, extend the computation step with the new metric, add it to the format template, and add a column to your history sheet. Because the workflow is modular — pull, compute, format, deliver — each change touches only one or two nodes. This is why building it cleanly the first time matters.

### Is it safe to connect n8n to my production CRM?

Yes, with normal precautions: use OAuth rather than API keys where available, connect with a dedicated integration user that has only the permissions the workflow needs, and never store credentials in workflow notes or code. n8n encrypts stored credentials. Start with read-only operations (like this report) before building workflows that write data back.

## Conclusion

You now have the complete blueprint: define the KPIs, connect the data, schedule the run, compute the numbers, format a digest humans will read, store history for trends, deliver it, and wrap it all in error handling you have actually tested.

The first build takes an afternoon. Every report after that takes zero minutes of human time and arrives more consistently than any manual process. More importantly, you now own a reusable pattern — scheduled pull, compute, format, deliver — that applies to marketing reports, support summaries, financial digests, and anything else your business measures repeatedly.

Build this one, get it trusted, and the next automation gets approved a lot faster. That is how an automation practice grows: one reliable workflow at a time.
