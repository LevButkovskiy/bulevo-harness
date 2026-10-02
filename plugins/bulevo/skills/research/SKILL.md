---
name: research
description: Research how to solve a problem before writing a spec, whether a product feature or a technical choice such as a rewrite or a library. Studies analogs, experience and best practices through web researcher subagents, compares 2–4 options and recommends one. The chosen option feeds /bulevo:task.
argument-hint: "[topic or problem]"
disable-model-invocation: true
---

# Research

The topic: $ARGUMENTS

Your job in this skill is to find the best way to solve a problem the user already understands and to help
them pick one. **Write no code, no spec, and ask nothing about implementation here.** The spec comes after,
from `/bulevo:task`.

**Language.** Every message, the report and the question about the choice go in the language the user
writes in, not English, unless the user writes in English.

## 1. Learn the product

Read what the session already has about the product: the CLAUDE.md files, product docs, the project memory.
Note what the product is, who uses it, its positioning and its constraints (stack, design system, paid
features, markets).

## 2. Decide what kind of question this is

The kind sets where to look and how to compare. Two common kinds, as examples, not a closed list:

| Kind | Directions for researchers | Criteria |
|---|---|---|
| Product or UI: a feature, a screen, a flow | Direct analogs; UX guidelines and best practices; adjacent products | Value for the user; UX and look |
| Technical: a rewrite, a migration, a framework, library or architecture | Teams that made the same choice and what came of it; comparison of the candidates from docs, benchmarks and issue trackers; pitfalls | Amount of work; risk of regressions, given the tests the project has; whether it can be done gradually; payoff for maintenance and the team |

Keep every criterion of the kind as its own column, phrased for the question's goal, and add any the
question needs. For any other kind, pick 2–3 directions and the criteria that decide it the same way.
Always compare by rough cost, risks, and fit with the current product and stack as well.

## 3. Learn what exists

If the question is about code that exists (the feature, a similar screen, the project being rewritten),
delegate to the `bulevo:scout` subagent with a brief for what this decision needs. For a feature, what it
does today. For a technical choice, the size and boundaries of the modules, how tightly the code is tied to
what would change, which tests exist, and what would move easily or hard. The options are compared with
what exists. Don't design the code.

## 4. Ask only about the goal and the plans

Facts about today (who maintains the code, the stack, the audience) may come from the code, the docs and
the memory. The goal and the plans that decide between options (team growth, load, deadlines) come only
from the user: if the user hasn't stated them, ask in one short round before researching. Don't infer them
from facts about today. Use the AskUserQuestion tool: at most 4 questions, 2–4 options each, recommended
option first. If that tool isn't available, ask in plain text and stop. Ask nothing that the research
itself should answer, and nothing about implementation.

## 5. Gather material

Delegate to 2–3 `bulevo:researcher` subagents in parallel, in one message, one direction from step 2 each.
Give each the topic, its direction and what to look for, and the context from steps 1 and 3. Only a
researcher looking at screens may use the browser, and only when the session has one; tell the others to
use web search and fetch. Read their reports; open a source yourself before a recommendation rests on it.

## 6. Compare options

Build 2–4 options from the material. One of them is always the simplest option that works; for a change to
something that exists, that may be keeping it and fixing what hurts. Compare them by the criteria from
step 2, and decide which one you would recommend, with reasons and source links; it is shown only in step
9. If sources were thin, say so instead of padding.

## 7. Write the report

Create `.claude/research/<YYYY-MM-DD>-<short-slug>.md` under the directory the session started in, in the
user's language:

```markdown
# <Topic>

## Problem
What the user wants to solve, for whom, and the constraints that apply.

## Today
Only when the question is about something that exists: what it is and does now.

## Analogs
Comparable products, or teams that made the same choice, and what came of it, each with a link.

## Best practices
Practices, guidelines and pitfalls, each with a source.

## Options
Every option compared by the same criteria, in whatever form reads best. Then a short description of each
option.

## Sources
Every URL used.
```

No screenshots: links and descriptions only. The recommendation is added in step 9.

## 8. Publish and compare

The user first needs to understand how the options differ, and decides only after that.

1. If the session has the Artifact tool, publish the report as a private Artifact page by that tool's own
   rules. Without it, give the file path.
2. Show the comparison in whatever form makes the difference clearest: the Artifact page, a table, a
   diagram. Cover the same points for every option, in plain words: what we do, how long it takes, what
   can break, what the code and the work look like after, and what it opens or closes later. Say which
   factors favor which option ("if the team grows, C").
3. In the message, give the report path and the page link, and invite questions.

This message has no recommendation and no question about the choice. Stop there and answer questions
from the report and its sources.

## 9. Recommend and ask for the choice

When the user says they understand the options or asks which to take, add to the report, before
Sources:

```markdown
## Recommendation
The option, the reasons, each assumption it rests on on its own line, and what would change the choice.
```

Republish the Artifact if there is one, and give the recommendation in the message. Ask which option to
take, recommended option first, in plain text, not with AskUserQuestion: its short labels hide the
difference between the options. Stop there.

## 10. Record the choice

When the user picks an option, add to the report:

```markdown
## Choice
The chosen option, and any change the user asked for.
```

Write the heading in the user's language. Republish the Artifact if there is one. Then suggest
`/bulevo:task <report path>`, preferably in a fresh session.
