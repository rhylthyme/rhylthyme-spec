# Changelog

All notable changes to the Rhylthyme specification package are documented
here. Schema files are never edited in place once shipped; a new version is a
new file, byte-copied to `rhylthyme-server/static/schema/` and
`rhylthyme-mcp/static/schema/` (checked by `tools/check_mirrors.sh`).

## Package 0.2.3-alpha - 2026-10-10: step alerts

A third additive amendment to the shipped program schemas, made in place on
the same terms as 0.2.1-alpha: the new property is optional, so every
document that was valid stays valid (rhylthyme/rhylthyme-spec#2, item 3).

### Added
- Program schemas 0.2.0-alpha and 0.3.0-alpha: optional step `alerts`, an
  array (at least one) of `definitions/alert`
  `{event, offsetSeconds?, message?, level?}`: `event` is `start | end` of
  the step itself, `offsetSeconds` a signed number or time string relative to
  it (`"-2m"` = two minutes before; default 0), `message` plain text of 1-200
  characters (the runner derives one when it is absent) and `level`
  `notice | alarm` (default `notice`; `alarm` may escalate to a device alarm
  where the person enabled alarms). Alerts are self-anchored, so replicate
  expansion copies them onto every instance. A before-start alert on a manual
  step and a before-end alert on an indefinite step cannot be projected and
  never fire; validators warn about both.

## Package 0.2.2-alpha - 2026-10-05: instrument phase actions, any driver

Another additive amendment to the shipped program and runs schemas, made in
place on the same terms as 0.2.1-alpha: every addition is optional, so every
document that was valid stays valid.

### Added
- Program schemas 0.2.0-alpha and 0.3.0-alpha: `instrument` moves to
  `definitions/instrument` and gains phase actions, each
  `{command, params?, tool?, timeoutSeconds?}` (`definitions/instrumentAction`):
  `start` (sent in order when the step starts), `until` (one call whose reply
  ends the step, instead of `command`), `end` (sent in order when the step
  ends, however it ends) and `onAbort` (sent if the step fails or the run is
  aborted, instead of the drivers' default safe stops). `command` and
  `until` are exclusive; a step needs at least one of `command`, `until`,
  `start` or `end`. A step with only `start`/`end` runs on its own duration.
- Runs schema 0.1.0-alpha: an instrument reply may carry `phase`
  (`start | call | until | end | onAbort | pause | resume`), `tool` and
  `command`; the step's `command` is empty when it has only start/end
  actions.

### Changed
- Wording is driver-neutral: a workcell maps each tool to galago-tools or
  LabMCP (rhylthyme-labmcp). `toolType` may name a LabMCP server package
  (`labmcp-ika`) as well as a galago tool type.

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
