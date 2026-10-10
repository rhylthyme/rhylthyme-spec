"""
Load every schema shipped by rhylthyme-spec and validate one sample document
of each type against it.

Run with:  cd rhylthyme-spec && python -m pytest -q tests/
"""

import glob
import json
import os

import jsonschema
import pytest

import rhylthyme_spec

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMAS_DIR = os.path.join(HERE, "..", "src", "rhylthyme_spec", "schemas")
EXAMPLES_DIR = os.path.join(HERE, "..", "..", "rhylthyme-examples")


def _load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator(path):
    schema = _load(path)
    jsonschema.Draft7Validator.check_schema(schema)
    return jsonschema.Draft7Validator(schema)


def _errors(validator, document):
    return [
        f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in validator.iter_errors(document)
    ]


# --------------------------------------------------------------- every schema


def test_every_schema_file_is_valid_json_schema():
    files = sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*.json")))
    assert files, "no schema files found"
    for path in files:
        _validator(path)


def test_schema_path_helpers_point_at_shipped_files():
    for getter in (
        rhylthyme_spec.get_program_schema_path,
        rhylthyme_spec.get_environment_schema_path,
        rhylthyme_spec.get_runs_schema_path,
    ):
        path = getter()
        assert os.path.isfile(path), path
    assert rhylthyme_spec.get_runs_schema_path().endswith("runs_schema_0.1.0-alpha.json")
    assert "get_runs_schema_path" in rhylthyme_spec.__all__


# ------------------------------------------------------------------- program


def test_program_schema_accepts_an_example_program():
    sample = os.path.join(EXAMPLES_DIR, "programs", "breakfast_schedule.json")
    if not os.path.isfile(sample):
        pytest.skip("rhylthyme-examples not checked out beside rhylthyme-spec")
    validator = _validator(rhylthyme_spec.get_program_schema_path())
    assert _errors(validator, _load(sample)) == []


def test_program_schema_rejects_program_without_tracks():
    validator = _validator(rhylthyme_spec.get_program_schema_path())
    assert _errors(validator, {"programId": "x", "name": "x"}) != []


# ------------------------------------------------------------- step alerts

PROGRAM_SCHEMAS = ["program_schema_0.2.0-alpha.json", "program_schema_0.3.0-alpha.json"]

ALERT_PROGRAM = {
    "programId": "alerts",
    "name": "Alerts",
    "resourceConstraints": [],
    "tracks": [
        {
            "trackId": "t",
            "name": "T",
            "steps": [
                {
                    "stepId": "bake",
                    "name": "Bake",
                    "startTrigger": {"type": "programStart"},
                    "duration": {"type": "fixed", "seconds": 600},
                    "alerts": [
                        {"event": "end", "offsetSeconds": "-2m", "message": "Nearly done"},
                        {"event": "start"},
                        {"event": "end", "offsetSeconds": 0, "level": "alarm"},
                        {"event": "end", "offsetSeconds": "1h30m", "level": "notice"},
                    ],
                }
            ],
        }
    ],
}


def _alert_program(alert):
    program = json.loads(json.dumps(ALERT_PROGRAM))
    program["tracks"][0]["steps"][0]["alerts"] = [alert]
    return program


@pytest.mark.parametrize("schema", PROGRAM_SCHEMAS)
def test_program_schemas_accept_step_alerts(schema):
    validator = _validator(os.path.join(SCHEMAS_DIR, schema))
    assert _errors(validator, ALERT_PROGRAM) == []


@pytest.mark.parametrize("schema", PROGRAM_SCHEMAS)
@pytest.mark.parametrize(
    "alert",
    [
        {"event": "middle"},
        {"event": "end", "level": "siren"},
        {"event": "end", "sound": "chime"},
        {"event": "start", "message": ""},
        {"event": "start", "message": "x" * 201},
        {"offsetSeconds": -60},
        {"event": "end", "offsetSeconds": True},
    ],
)
def test_program_schemas_reject_bad_alerts(schema, alert):
    validator = _validator(os.path.join(SCHEMAS_DIR, schema))
    assert _errors(validator, _alert_program(alert)) != []


@pytest.mark.parametrize("schema", PROGRAM_SCHEMAS)
def test_program_schemas_reject_empty_alerts(schema):
    validator = _validator(os.path.join(SCHEMAS_DIR, schema))
    program = json.loads(json.dumps(ALERT_PROGRAM))
    program["tracks"][0]["steps"][0]["alerts"] = []
    assert _errors(validator, program) != []


# --------------------------------------------------------------- environment


def test_environment_schema_accepts_an_example_environment():
    sample = os.path.join(EXAMPLES_DIR, "environments", "home_kitchen.json")
    if not os.path.isfile(sample):
        pytest.skip("rhylthyme-examples not checked out beside rhylthyme-spec")
    validator = _validator(rhylthyme_spec.get_environment_schema_path())
    assert _errors(validator, _load(sample)) == []


# ---------------------------------------------------------------------- runs


SAMPLE_RUN = {
    "schemaVersion": "0.1.0-alpha",
    "runId": "2026-09-11T16:02:11Z-8f3a",
    "programId": "thanksgiving-one-oven",
    "programVersion": "sha256:" + "ab" * 32,
    "runtime": {"kind": "cli", "version": "0.1.0-alpha", "clockMode": "wall", "speed": 1},
    "environmentId": "home-kitchen",
    "startedAt": "2026-09-11T16:02:11.000Z",
    "endedAt": "2026-09-11T20:14:40.000Z",
    "outcome": "completed",
    "context": {"serves": "8", "actors": 2, "userTags": {"oven": "gas", "turkeyKg": 6.4}},
    "steps": [
        {
            "stepId": "turkey-prep",
            "instance": 1,
            "planned": {"start": 0, "end": 1200, "durationType": "fixed", "seconds": 1200},
            "actual": {"start": 0.1, "end": 1203.4},
            "endedBy": "timer",
            "triggerFiredAt": 0.1,
            "pausedSeconds": 0,
        },
        {
            "stepId": "turkey-roast",
            "instance": 1,
            "planned": {
                "start": 1200,
                "end": 11100,
                "durationType": "indefinite",
                "defaultSeconds": 9900,
            },
            "actual": {"start": 1203.4, "end": 12610.0},
            "endedBy": "executor",
            "triggerFiredAt": 1203.4,
            "waitedOn": ["turkey-prep"],
            "pausedSeconds": 0,
            "notes": "ran cold, oven door opened twice",
        },
        {
            "stepId": "potatoes-boil",
            "instance": 1,
            "planned": {
                "start": 9300,
                "end": 10500,
                "durationType": "variable",
                "minSeconds": 900,
                "maxSeconds": 1500,
                "defaultSeconds": 1200,
            },
            "actual": {"start": 9310},
            "pausedSeconds": 42.5,
        },
        {
            "stepId": "serve",
            "planned": {"start": 13500, "end": 13800, "durationType": "fixed", "seconds": 300},
        },
    ],
}


def test_runs_schema_accepts_sample_record():
    validator = _validator(rhylthyme_spec.get_runs_schema_path())
    assert _errors(validator, SAMPLE_RUN) == []


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r.pop("programVersion"),
        lambda r: r.update(programVersion="md5:abc"),
        lambda r: r.update(outcome="crashed"),
        lambda r: r["runtime"].update(kind="ios"),
        lambda r: r["runtime"].update(clockMode="guess"),
        lambda r: r["steps"][0].update(endedBy="ghost"),
        lambda r: r["steps"][0].pop("endedBy"),  # actual.end present -> endedBy required
        lambda r: r["steps"][0]["planned"].update(durationType="forever"),
        lambda r: r["steps"][0].update(pausedSeconds=-1),
        lambda r: r.update(runId="not-a-run-id"),
    ],
)
def test_runs_schema_rejects_bad_records(mutate):
    validator = _validator(rhylthyme_spec.get_runs_schema_path())
    record = json.loads(json.dumps(SAMPLE_RUN))
    mutate(record)
    assert _errors(validator, record) != []
