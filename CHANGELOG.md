# Changelog

All notable changes to the Rhylthyme specification package are documented
here. Schema files are never edited in place once shipped; a new version is a
new file, byte-copied to `rhylthyme-server/static/schema/` and
`rhylthyme-mcp/static/schema/` (checked by `tools/check_mirrors.sh`).

## Package 0.2.1-alpha - 2026-09-24: galago instrument steps

An additive amendment to shipped schema files, made in place as an exception
to the rule above: every addition is optional, so no document that was valid
before becomes invalid, and readers that ignore the new fields are unaffected.

### Added
- Program schemas 0.2.0-alpha and 0.3.0-alpha: optional step `instrument`
  `{tool, command, params?, toolType?, timeoutSeconds?}`, a galago-tools
  command that the runner (`rhylthyme run --workcell`, via rhylthyme-galago)
  sends when the step starts; the step ends when the instrument replies.
- Runs schema 0.1.0-alpha: `endedBy` values `instrument` (the instrument
  reported its command finished) and `skipped` (the command failed and the
  operator marked the step done); optional step `instrument`
  `{tool, command, replies: [{attempt, at, code, errorMessage?, metadata?}]}`.
  Tool addresses are never recorded.

## Runs schema 0.1.0-alpha - 2026-09-13

### Added
- `runs_schema_0.1.0-alpha.json`: a separate document type for execution
  history — one record per run with `planned` timings frozen at run start
  beside `actual` timings, `endedBy` (`executor | timer | trigger | abort`),
  `triggerFiredAt`, `waitedOn`, `pausedSeconds`, `outcome`
  (`completed | aborted | abandoned`), `runtime {kind, version, clockMode,
  speed}` and `programVersion` (`sha256:` of the program's canonical JSON).
  Step times are seconds from `startedAt`. OWL-Time `$comment`s describe the
  run and each step's actual interval as `time:ProperInterval`s.
- Python: `get_runs_schema_path()`.
- First test module, `tests/test_schemas.py`: loads every shipped schema and
  validates a sample document of each type.

## Program schema 0.3.0-alpha - 2026-09-13

### Added
- `instances` (`"each" | "all" | "any"`, default `"all"`) on `afterStep` and
  `afterStepWithBuffer`, including inside compound triggers, with OWL-Time
  `$comment`s: `"all"` is a barrier (`time:intervalAfter` the latest
  `time:hasEnd`), `"each"` pairs instance *i* with instance *i*
  (`time:intervalMetBy` / `time:intervalAfter` per pair), `"any"` follows the
  earliest `time:hasEnd`.
- `maxInFlight` (integer >= 1, <= `count`) on step-level `replicates`: the
  maximum number of instances that may be in flight, i.e. started but not yet
  ended in every `instances: "each"` descendant. Annotated in OWL-Time as a
  bound on the number of `time:ProperInterval`s, each spanning from an
  instance's `time:hasBeginning` to the latest `time:hasEnd` among its paired
  descendants, that may `time:intervalOverlaps` any given instant. Omitting it
  means unbounded, which is the pre-`0.3.0` behaviour.
- `schemaVersion` default is `"0.3.0-alpha"`; `0.1.0`, `0.2.0` and
  `0.2.0-alpha` programs remain valid and resolve to identical times.
- Python: `get_program_schema_path(version="0.2.0-alpha")` and
  `PROGRAM_SCHEMA_VERSIONS`. The default path is unchanged.

## Program schema 0.2.0-alpha

- Choice branching (`choice` on steps, `choiceId` on `afterStep`),
  `replicates` on tracks and steps, compound triggers, `onAbort`.
