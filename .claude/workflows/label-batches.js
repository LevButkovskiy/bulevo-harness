export const meta = {
  name: 'label-batches',
  description: 'Label batched Claude Code session digests in parallel, then finish any batch that came back short',
  phases: [
    { title: 'Label', detail: 'one agent per batch of session digests' },
    { title: 'Finish short batches', detail: 'label the ids a batch left out' },
  ],
}

const BATCH_RESULT = {
  type: 'object',
  required: ['labeled', 'expected', 'patterns'],
  properties: {
    labeled: { type: 'integer', description: 'lines in the output file that parse as JSON' },
    expected: { type: 'integer', description: 'ids in the batch file; 0 if the file does not exist' },
    missing: { type: 'array', items: { type: 'string' }, description: 'session ids with no line yet' },
    patterns: { type: 'array', items: { type: 'string' }, description: '2-3 short recurring patterns across this batch' },
  },
}

const out = args && args.out
const count = args && args.batches
if (!out || !count) {
  throw new Error('Pass args: { "out": "<data dir>", "batches": <number of batch files>, "rules": "<path, optional>" }')
}
const rules = (args && args.rules) || 'tools/transcripts/LABELING.md'
const batches = Array.from({ length: count }, (_, i) => i + 1)

const idsFile = n => `${out}/batches/batch-${n}.txt`
const labelsFile = n => `${out}/labels/batch-${n}.jsonl`

const tail = n => `Finally read ${labelsFile(n)} back: return the number of lines that parse as JSON, the number of ids in the batch, any ids still without a line, and 2-3 short recurring patterns across the batch, in the language the sessions are written in. If ${idsFile(n)} does not exist, return 0 for both counts and say so in the patterns.`

const labelPrompt = n => `Label Claude Code session digests. Repo root: the current directory.
1. Read the rules in ${rules} and follow them exactly.
2. The session ids to label are in ${idsFile(n)}, one per line.
3. For each id, read ${out}/digests/<id>.md in full. Use Read with offset and limit on large files, and do not skip parts: corrections often appear late in a session.
4. Append exactly one JSON line per session to ${labelsFile(n)}: valid JSON per line, UTF-8, keys in the order the rules give. Write incrementally so progress survives an interruption.
5. Do not read raw transcripts under ~/.claude, and do not modify anything else.
${tail(n)}`

const finishPrompt = n => `An earlier agent labelled only part of a batch of Claude Code session digests. Repo root: the current directory.
1. Read the rules in ${rules} and follow them exactly.
2. Compare the ids in ${idsFile(n)} with the session_id values already in ${labelsFile(n)}.
3. For every id that has no line yet, read ${out}/digests/<id>.md in full and append one JSON line to ${labelsFile(n)}. Leave the existing lines untouched.
4. Do not read raw transcripts under ~/.claude, and do not modify anything else.
${tail(n)}`

const complete = r => !!r && typeof r.labeled === 'number' && r.labeled >= r.expected
const merge = (n, prev, next) => ({ ...(prev || {}), ...(next || {}), batch: n })

const retry = (round, r, n) =>
  complete(r)
    ? r
    : agent(finishPrompt(n), {
        phase: 'Finish short batches',
        label: `batch-${n} (retry ${round})`,
        model: 'sonnet',
        schema: BATCH_RESULT,
      }).then(x => merge(n, r, x))

const results = await pipeline(
  batches,
  n =>
    agent(labelPrompt(n), {
      phase: 'Label',
      label: `batch-${n}`,
      model: 'sonnet',
      schema: BATCH_RESULT,
    }).then(r => merge(n, null, r)),
  (r, n) => retry(1, r, n),
  (r, n) => retry(2, r, n),
)

const done = results.filter(Boolean)
const short = done.filter(r => !complete(r))
const lost = batches.filter((_, i) => !results[i])

log(`${done.reduce((n, r) => n + (r.labeled || 0), 0)} sessions labelled across ${batches.length} batches`)
for (const r of short) log(`batch-${r.batch}: ${r.labeled} of ${r.expected} labelled, still short`)
for (const n of lost) log(`batch-${n}: no result, label it by hand`)

return { batches: done, incomplete: short.map(r => r.batch), lost }
