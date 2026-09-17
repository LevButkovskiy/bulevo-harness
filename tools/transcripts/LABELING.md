# Session labeling instructions

You label Claude Code sessions from digests produced by `plugins/bulevo/scripts/transcripts.py`. The goal is to find where the
agent failed the user, what the work was, and which sessions can become repeatable benchmark tasks.
Write every free-text field short and in the language the user writes in within the sessions.

A digest shows each human prompt, the tools the agent used before the next prompt, flags
(INTERRUPTED, REJECTED-TOOL, tool-errors), and the agent's last reply of that turn.

## Judge only from evidence

- A correction is a user prompt that reacts to something the agent did wrong or missed. Evidence is the
  user's own words. "Продолжай", "Создай MR", a new unrelated request, or approving a plan are not
  corrections.
- If a digest is too clipped to tell, say so in `notes` instead of guessing.
- Do not judge code quality you cannot see.

## Output

One JSON object per session, one per line (JSONL), written to the output file you are given.
No prose outside the file. Keys, in this order:

```json
{
  "session_id": "…",
  "summary": "одна фраза: что пытались сделать и чем кончилось",
  "type": "bug | feature | refactor | ui_design | architecture | research | ops | review_audit | planning | free_exploration | harness_meta | mixed",
  "size": "S | M | L | XL",
  "outcome": "done | done_after_corrections | partial | abandoned | unclear",
  "task_clarity": "clear | vague | evolving",
  "requirements_source": "user_prompt | spec_file | tracker | mixed",
  "corrections": [
    {
      "turn": 3,
      "category": "misunderstood_task | wrong_approach | bug_in_result | incomplete | didnt_verify | ignored_instruction | overengineering | scope_creep | standards_style | ui_quality | outdated_tech | env_tooling | too_many_questions | should_have_asked | other",
      "evidence": "короткая цитата пользователя, до 150 символов",
      "harness_fix": "какой механизм предотвратил бы это: check | hook | skill | spec | reviewer | question | tool | model | none"
    }
  ],
  "agent_questions_useful": "yes | partly | no | none_asked",
  "agent_pushback": "none | useful | excessive",
  "benchmark_candidate": {
    "fit": "strong | possible | no",
    "why": "почему да или нет",
    "has_commits": true,
    "verifiable_by": "tests | typecheck | screenshot | manual_review | unclear"
  },
  "notes": ""
}
```

## Size guide

- S: one focused change, under ~5 prompts
- M: a feature or bug touching several files, one session
- L: multi-part work, design plus implementation, many prompts
- XL: long multi-day session or several distinct tasks in one

## Benchmark fit

`strong` only when all hold: a task statement that stands alone (first prompt or a spec), a result the
user accepted, commits exist so the before/after state is recoverable, and success can be checked
without the user's memory. Free exploration, brainstorming and "что ещё добавить" sessions are `no`.
