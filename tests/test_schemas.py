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


# --------------------------------------------------------- runs: video records

# A record made from a video: every time is seconds of the video's media
# timeline. The second step never happened, so it has no `actual`; the first
# carries a dataset's error tags in `notes`.
VIDEO_RUN = {
    "schemaVersion": "0.1.0-alpha",
    "runId": "2026-11-05T00:00:00Z-1c7e",
    "programId": "video-recipe",
    "programVersion": "sha256:" + "cd" * 32,
    "runtime": {"kind": "video", "version": "0.1.0", "clockMode": "media", "speed": 1},
    "startedAt": "2026-11-05T00:00:00Z",
    "outcome": "completed",
    "steps": [
        {
            "stepId": "n1",
            "planned": {
                "start": 0,
                "end": 60,
                "durationType": "variable",
                "minSeconds": 30,
                "maxSeconds": 120,
                "defaultSeconds": 60,
            },
            "actual": {"start": 3.37, "end": 71.04},
            "endedBy": "annotation",
            "notes": "Measurement Error: used too much of an ingredient",
        },
        {
            "stepId": "n2",
            "planned": {"start": 60, "end": 90, "durationType": "fixed", "seconds": 30},
        },
        {
            "stepId": "n3",
            "planned": {"start": 90, "end": 150, "durationType": "fixed", "seconds": 60},
            "actual": {"start": 72.5, "end": 140.0},
            "endedBy": "annotation",
        },
    ],
}


def _video_run(ended_by="annotation"):
    record = json.loads(json.dumps(VIDEO_RUN))
    for step in record["steps"]:
        if "endedBy" in step:
            step["endedBy"] = ended_by
    return record


@pytest.mark.parametrize("ended_by", ["annotation", "observer"])
def test_runs_schema_accepts_video_records(ended_by):
    validator = _validator(rhylthyme_spec.get_runs_schema_path())
    assert _errors(validator, _video_run(ended_by)) == []


def test_runs_schema_accepts_observer_and_annotation_ends_in_one_record():
    validator = _validator(rhylthyme_spec.get_runs_schema_path())
    record = _video_run("annotation")
    record["steps"][2]["endedBy"] = "observer"  # a dataset step edited by hand
    assert _errors(validator, record) == []


def test_runs_schema_accepts_new_values_in_wall_records():
    # The amendment adds enum values; it does not tie them to each other.
    validator = _validator(rhylthyme_spec.get_runs_schema_path())
    record = json.loads(json.dumps(SAMPLE_RUN))
    record["steps"][1]["endedBy"] = "observer"
    assert _errors(validator, record) == []


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r["runtime"].update(kind="youtube"),
        lambda r: r["runtime"].update(kind="Video"),
        lambda r: r["runtime"].update(clockMode="video"),
        lambda r: r["runtime"].update(clockMode="frames"),
        lambda r: r["steps"][0].update(endedBy="label"),
        lambda r: r["steps"][0].update(endedBy="watcher"),
        lambda r: r["steps"][0].update(endedBy="Observer"),
        lambda r: r["steps"][0].pop("endedBy"),  # actual.end present -> endedBy required
        lambda r: r["runtime"].update(fps=29.97),  # runtime still closed
        lambda r: r.update(videoUrl="https://example.com/v.mp4"),  # root still closed
        lambda r: r["steps"][0].update(extraIntervals=[]),  # belongs to the timeline row
        lambda r: r["steps"][0]["actual"].update(frame=101),  # actual still closed
        lambda r: r["steps"][0]["actual"].update(start=-0.5),
    ],
)
def test_runs_schema_rejects_bad_video_records(mutate):
    validator = _validator(rhylthyme_spec.get_runs_schema_path())
    record = _video_run()
    assert _errors(validator, record) == []  # only the mutation makes it invalid
    mutate(record)
    assert _errors(validator, record) != []


def _schema_node(schema, path):
    node = schema
    for key in path:
        node = node[key]
    return node


@pytest.mark.parametrize(
    "path, phrases",
    [
        (("properties", "runtime", "properties", "kind"), ["video", "marking screen"]),
        (
            ("properties", "runtime", "properties", "clockMode"),
            ["media", "media timeline", "first frame"],
        ),
        (
            ("properties", "startedAt"),
            ["media", "recording began", "timeline was made"],
        ),
        (("properties", "outcome"), ["media", "video shows the procedure to its end"]),
        (("definitions", "stepRecord", "properties", "actual"), ["never happened"]),
        (
            ("definitions", "stepRecord", "properties", "endedBy"),
            ["annotation", "dataset label", "observer", "suggestion"],
        ),
        (("definitions", "stepRecord", "properties", "notes"), ["error tags"]),
    ],
)
def test_runs_schema_describes_media_records(path, phrases):
    description = _schema_node(_load(rhylthyme_spec.get_runs_schema_path()), path)[
        "description"
    ]
    for phrase in phrases:
        assert phrase in description, f"{'/'.join(path)}: missing {phrase!r}"


def test_suggestions_schema_says_what_a_repeated_step_means():
    # The harness scores repeats as occurrences and the marking screen fills
    # replicate instances from them; one rule, stated once, for both.
    schema = _load(rhylthyme_spec.get_video_suggestions_schema_path())
    description = schema["properties"]["steps"]["description"]
    for phrase in ["occurrences", "ordered by start", "instances in order", "extra intervals"]:
        assert phrase in description, f"steps: missing {phrase!r}"


# --------------------------------------------------------- video suggestions


def test_video_suggestions_schema_path_helper_points_at_shipped_file():
    path = rhylthyme_spec.get_video_suggestions_schema_path()
    assert os.path.isfile(path), path
    assert path.endswith("video_suggestions_schema_0.1.0-alpha.json")
    assert "get_video_suggestions_schema_path" in rhylthyme_spec.__all__


# The design's example, with real hashes, plus a step the proposer thinks did
# not happen (no start or end) and a step proposed twice (a repeated step).
SAMPLE_SUGGESTIONS = {
    "schemaVersion": "0.1.0-alpha",
    "programVersion": "sha256:" + "ab" * 32,
    "video": {"sha256": "0123456789abcdef" * 4, "durationSeconds": 1234.5},
    "proposer": {"name": "timer-reanchored", "version": "0.1.0", "settings": {}},
    "createdAt": "2026-11-05T00:00:00Z",
    "steps": [
        {"stepId": "n3", "present": True, "start": 12.0, "end": 80.5, "confidence": 0.4},
        {"stepId": "n4", "present": False, "confidence": 0.9},
        {"stepId": "n5", "present": True, "start": 0, "end": 0, "confidence": 0},
        {"stepId": "n5", "present": True, "start": 300, "end": 320.25, "confidence": 1},
    ],
}


def _suggestions_validator():
    return _validator(rhylthyme_spec.get_video_suggestions_schema_path())


def test_video_suggestions_schema_accepts_sample_document():
    assert _errors(_suggestions_validator(), SAMPLE_SUGGESTIONS) == []


def test_video_suggestions_schema_accepts_minimal_document():
    minimal = {
        "programVersion": "sha256:" + "0" * 64,
        "video": {"sha256": "f" * 64, "durationSeconds": 0.04},
        "proposer": {"name": "uniform-split", "version": "0.1.0"},
        "createdAt": "2026-11-05T12:34:56.789Z",
        "steps": [{"stepId": "s1", "present": True, "start": 1, "end": 2}],
    }
    assert _errors(_suggestions_validator(), minimal) == []


def test_video_suggestions_schema_accepts_free_form_proposer_settings():
    document = json.loads(json.dumps(SAMPLE_SUGGESTIONS))
    document["proposer"]["settings"] = {
        "model": "any",
        "frameEverySeconds": 2,
        "frameSize": [448, 252],
        "anchors": {"firstStart": 3.2},
    }
    assert _errors(_suggestions_validator(), document) == []


def _step(document, index=0):
    return document["steps"][index]


@pytest.mark.parametrize(
    "mutate",
    [
        # required root fields
        lambda d: d.pop("programVersion"),
        lambda d: d.pop("video"),
        lambda d: d.pop("proposer"),
        lambda d: d.pop("createdAt"),
        lambda d: d.pop("steps"),
        lambda d: d.update(steps={}),
        lambda d: d.update(createdAt=1730764800),
        lambda d: d.update(timelineId="x"),  # root closed
        # programVersion: same pattern as the runs schema
        lambda d: d.update(programVersion="md5:abc"),
        lambda d: d.update(programVersion="ab" * 32),
        lambda d: d.update(programVersion="sha256:" + "AB" * 32),
        lambda d: d.update(programVersion="sha256:" + "a" * 63),
        # video
        lambda d: d["video"].pop("sha256"),
        lambda d: d["video"].pop("durationSeconds"),
        lambda d: d["video"].update(sha256="sha256:" + "ab" * 32),  # the key names it
        lambda d: d["video"].update(sha256="AB" * 32),
        lambda d: d["video"].update(sha256="a" * 65),
        lambda d: d["video"].update(durationSeconds=0),
        lambda d: d["video"].update(durationSeconds=-1),
        lambda d: d["video"].update(url="https://example.com/v.mp4"),  # video closed
        # proposer
        lambda d: d["proposer"].pop("name"),
        lambda d: d["proposer"].pop("version"),
        lambda d: d["proposer"].update(name=""),
        lambda d: d["proposer"].update(version=""),
        lambda d: d["proposer"].update(settings=[]),
        lambda d: d["proposer"].update(author="x"),  # proposer closed
        # steps
        lambda d: _step(d).pop("stepId"),
        lambda d: _step(d).pop("present"),
        lambda d: _step(d).update(present="yes"),
        lambda d: _step(d).pop("start"),  # present: true needs start
        lambda d: _step(d).pop("end"),  # present: true needs end
        lambda d: _step(d, 1).update(start=1.0),  # present: false forbids start
        lambda d: _step(d, 1).update(end=2.0),  # present: false forbids end
        lambda d: _step(d).update(start=-0.1),
        lambda d: _step(d).update(end="80s"),
        lambda d: _step(d).update(confidence=-0.01),
        lambda d: _step(d).update(confidence=1.01),
        lambda d: _step(d).update(confidence="high"),
        lambda d: _step(d).update(label="Chop"),  # step closed
    ],
)
def test_video_suggestions_schema_rejects_bad_documents(mutate):
    validator = _suggestions_validator()
    document = json.loads(json.dumps(SAMPLE_SUGGESTIONS))
    assert _errors(validator, document) == []  # only the mutation makes it invalid
    mutate(document)
    assert _errors(validator, document) != []
