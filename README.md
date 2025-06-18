# Rhylthyme Specification (Alpha)

**⚠️ ALPHA RELEASE** - This specification is in early development and may change significantly before the first stable release.

Standards and schema for a real-time program logistics description markup language.

## Version Information

- **Current Version**: 0.1.0a1 (Alpha)
- **Schema Version**: 0.1.0-alpha
- **Status**: Early development - breaking changes may occur

## Overview

Rhylthyme is a JSON-based markup language for describing real-time programs that coordinate multiple parallel tracks of work with resource constraints, timing dependencies, and flexible execution patterns. It's designed for scenarios like restaurant kitchens, laboratory workflows, manufacturing processes, and any situation requiring coordinated real-time execution.

## Alpha Release Notes

This alpha release includes:
- ✅ Basic program structure with tracks and steps
- ✅ Simplified "on" trigger syntax
- ✅ Resource constraints
- ✅ Variable and fixed duration types
- ✅ Batch processing with staggering
- 🔄 Environment integration (in progress)
- 🔄 Advanced validation rules (in progress)
- ❌ Resource specifications (planned)
- ❌ Environment schemas (planned)

## Schema Structure

The Rhylthyme schema defines programs as JSON objects with the following key components:

### Program-Level Properties

- **`programId`** (required): Unique identifier for the program
- **`name`** (required): Human-readable name
- **`description`**: Detailed description
- **`version`**: Program version number (should match schema version)
- **`environmentType`**: Type of environment (e.g., 'kitchen', 'laboratory')
- **`actors`**: Number of available workers/operators
- **`tracks`** (required): Array of parallel execution tracks
- **`resourceConstraints`** (required): Resource usage limits
- **`startTrigger`**: How the program begins execution

### Example: Restaurant Breakfast Service

```json
{
  "programId": "restaurant-breakfast",
  "name": "Restaurant Breakfast Service",
  "description": "Professional restaurant breakfast service workflow with coordinated cooking and plating",
  "version": "0.1.0-alpha",
  "environmentType": "kitchen",
  "actors": 2,
  "startTrigger": {
    "type": "manual"
  },
  "tracks": [
    {
      "trackId": "scrambled-eggs",
      "name": "Scrambled Eggs",
      "description": "Multiple orders of scrambled eggs",
      "batch_size": 3,
      "steps": [
        {
          "stepId": "eggs-crack-whisk",
          "name": "Crack and Whisk Eggs",
          "description": "Crack eggs into a bowl and whisk with salt and pepper",
          "task": "prep-work",
          "trigger": {
            "type": "programStart"
          },
          "duration": {
            "type": "fixed",
            "seconds": 60
          }
        },
        {
          "stepId": "eggs-heat-pan",
          "name": "Heat Pan",
          "description": "Place pan on stove and heat to medium",
          "trigger": {
            "on": "eggs-crack-whisk"
          },
          "duration": {
            "type": "variable",
            "minSeconds": 60,
            "maxSeconds": 120,
            "defaultSeconds": 90,
            "triggerName": "pan-ready"
          },
          "task": "stove-burner"
        }
      ]
    }
  ],
  "resourceConstraints": [
    {
      "task": "stove-burner",
      "maxConcurrent": 4,
      "description": "Maximum number of stove burners that can be used simultaneously"
    }
  ]
}
```

## Track Structure

Tracks represent parallel workflows within a program. Each track can have multiple steps and can be executed multiple times (batch processing).

### Track Properties

- **`trackId`** (required): Unique identifier
- **`name`** (required): Human-readable name
- **`description`**: Detailed description
- **`batch_size`**: Number of iterations (default: 1)
- **`stagger`**: Time delay between batch instances
- **`priority`**: Execution priority (lower = higher priority)
- **`steps`** (required): Array of sequential steps

### Example: Bacon Cooking Track

```json
{
  "trackId": "bacon",
  "name": "Bacon",
  "description": "Multiple orders of bacon",
  "batch_size": 2,
  "steps": [
    {
      "stepId": "bacon-prep",
      "name": "Prepare Bacon",
      "description": "Place bacon strips in cold pan",
      "task": "prep-work",
      "trigger": {
        "type": "programStart"
      },
      "duration": {
        "type": "fixed",
        "seconds": 60
      }
    },
    {
      "stepId": "bacon-cook",
      "name": "Cook Bacon",
      "description": "Cook bacon, flipping occasionally until crispy",
      "trigger": {
        "on": "bacon-prep"
      },
      "duration": {
        "type": "variable",
        "minSeconds": 480,
        "maxSeconds": 720,
        "defaultSeconds": 600,
        "triggerName": "bacon-done"
      },
      "task": "stove-burner"
    }
  ]
}
```

## Step Structure

Steps are the individual work units within a track. They define what work is done, how long it takes, and when it starts.

### Step Properties

- **`stepId`** (required): Unique identifier
- **`name`** (required): Human-readable name
- **`description`**: Detailed description
- **`task`**: Resource/tool required for this step
- **`trigger`** (required): When this step begins
- **`duration`** (required): How long the step takes
- **`resources`**: Array of required resources
- **`flex`**: Whether this step can expand to fill available time

### Trigger Types

#### 1. Program Start
```json
{
  "type": "programStart"
}
```
Step begins immediately when the program starts.

#### 2. On Another Step (Simplified Syntax)
```json
{
  "on": "eggs-crack-whisk"
}
```
Step begins when the specified step completes.

#### 3. On Step with Offset
```json
{
  "on": "eggs-crack-whisk",
  "offsetSeconds": 30
}
```
Step begins 30 seconds after the specified step completes.

#### 4. On Step Start Event
```json
{
  "on": "eggs-crack-whisk",
  "event": "start"
}
```
Step begins when the specified step starts (not when it completes).

#### 5. Manual Trigger
```json
{
  "type": "manual",
  "triggerName": "start-cooking"
}
```
Step begins when manually triggered.

### Duration Types

#### 1. Fixed Duration
```json
{
  "type": "fixed",
  "seconds": 60
}
```
Step takes exactly 60 seconds.

#### 2. Variable Duration
```json
{
  "type": "variable",
  "minSeconds": 480,
  "maxSeconds": 720,
  "defaultSeconds": 600,
  "triggerName": "bacon-done"
}
```
Step duration varies based on conditions, with manual completion trigger.

#### 3. Time String Format
```json
{
  "type": "fixed",
  "timeString": "2m30s"
}
```
Duration specified as a human-readable time string.

## Resource Constraints

Resource constraints limit how many instances of a task can run simultaneously.

```json
{
  "resourceConstraints": [
    {
      "task": "stove-burner",
      "maxConcurrent": 4,
      "description": "Maximum number of stove burners that can be used simultaneously"
    },
    {
      "task": "toaster",
      "maxConcurrent": 2,
      "description": "Maximum number of toasters that can be used simultaneously"
    }
  ]
}
```

## Advanced Features

### Batch Processing with Staggering

```json
{
  "trackId": "toast",
  "name": "Toast",
  "description": "Multiple orders of toast",
  "batch_size": 4,
  "stagger": "30s",
  "steps": [
    {
      "stepId": "toast-cook",
      "name": "Make Toast",
      "description": "Place bread in toaster and toast until golden brown",
      "trigger": {
        "type": "programStartOffset",
        "offsetSeconds": 120
      },
      "duration": {
        "type": "fixed",
        "seconds": 210
      },
      "task": "toaster"
    }
  ]
}
```

This creates 4 toast orders, each starting 30 seconds after the previous one.

### Flexible Steps

```json
{
  "stepId": "wait-for-eggs",
  "name": "Wait for Eggs",
  "description": "Flexible waiting period while eggs cook",
  "task": "waiting",
  "trigger": {
    "on": "eggs-start-cooking"
  },
  "duration": {
    "type": "variable",
    "minSeconds": 0,
    "maxSeconds": 300,
    "defaultSeconds": 180
  },
  "flex": true
}
```

Flexible steps can expand or contract to fill available time gaps.

## Environment Integration

Programs can reference environment definitions that specify available resources and their capabilities.

```json
{
  "programId": "restaurant-breakfast",
  "name": "Restaurant Breakfast Service",
  "version": "0.1.0-alpha",
  "environmentType": "kitchen",
  "environment": "restaurant-standard.json"
}
```

## Validation

The schema enforces:

- Required fields are present
- Step dependencies are valid
- Resource constraints are reasonable
- Duration values are positive
- Track and step IDs are unique within their scope

## Usage Examples

### Simple Sequential Workflow
```json
{
  "programId": "simple-cooking",
  "name": "Simple Cooking",
  "version": "0.1.0-alpha",
  "tracks": [
    {
      "trackId": "main",
      "name": "Main Track",
      "steps": [
        {
          "stepId": "prep",
          "name": "Preparation",
          "task": "prep-work",
          "trigger": {"type": "programStart"},
          "duration": {"type": "fixed", "seconds": 60}
        },
        {
          "stepId": "cook",
          "name": "Cooking",
          "task": "stove-burner",
          "trigger": {"on": "prep"},
          "duration": {"type": "fixed", "seconds": 300}
        }
      ]
    }
  ],
  "resourceConstraints": [
    {"task": "stove-burner", "maxConcurrent": 2}
  ]
}
```

### Complex Parallel Workflow
```json
{
  "programId": "breakfast-service",
  "name": "Breakfast Service",
  "version": "0.1.0-alpha",
  "actors": 3,
  "tracks": [
    {
      "trackId": "eggs",
      "name": "Eggs Station",
      "batch_size": 5,
      "stagger": "45s",
      "steps": [
        {
          "stepId": "eggs-prep",
          "name": "Prepare Eggs",
          "task": "prep-work",
          "trigger": {"type": "programStart"},
          "duration": {"type": "fixed", "seconds": 30}
        },
        {
          "stepId": "eggs-cook",
          "name": "Cook Eggs",
          "task": "stove-burner",
          "trigger": {"on": "eggs-prep"},
          "duration": {"type": "variable", "minSeconds": 120, "maxSeconds": 180, "defaultSeconds": 150}
        }
      ]
    },
    {
      "trackId": "bacon",
      "name": "Bacon Station",
      "batch_size": 3,
      "stagger": "60s",
      "steps": [
        {
          "stepId": "bacon-cook",
          "name": "Cook Bacon",
          "task": "stove-burner",
          "trigger": {"type": "programStartOffset", "offsetSeconds": 30},
          "duration": {"type": "fixed", "seconds": 600}
        }
      ]
    }
  ],
  "resourceConstraints": [
    {"task": "stove-burner", "maxConcurrent": 4},
    {"task": "prep-work", "maxConcurrent": 2}
  ]
}
```

### Advanced Trigger Examples

#### Cross-Track Dependencies
```json
{
  "stepId": "plate-breakfast",
  "name": "Plate Breakfast",
  "description": "Plate the complete breakfast when all components are ready",
  "task": "plating",
  "trigger": {
    "on": "eggs-cook",
    "on": "bacon-cook",
    "on": "toast-cook"
  },
  "duration": {"type": "fixed", "seconds": 30}
}
```

#### Offset from Step Completion
```json
{
  "stepId": "serve-breakfast",
  "name": "Serve Breakfast",
  "description": "Serve the plated breakfast after a brief rest period",
  "task": "service",
  "trigger": {
    "on": "plate-breakfast",
    "offsetSeconds": 15
  },
  "duration": {"type": "fixed", "seconds": 20}
}
```

#### Step Start Event
```json
{
  "stepId": "preheat-oven",
  "name": "Preheat Oven",
  "description": "Start preheating when cooking begins",
  "task": "oven",
  "trigger": {
    "on": "eggs-cook",
    "event": "start"
  },
  "duration": {"type": "fixed", "seconds": 300}
}
```

## Schema Files

- `schemas/program_schema_0.1.0-alpha.json` - Main program schema (Alpha version)
- `schemas/program_schema.json` - Latest program schema (symlink to alpha version)
- `schemas/environment_schema.json` - Environment definitions (coming soon)
- `schemas/resource_schema.json` - Resource specifications (coming soon)

## Migration Guide

### From Pre-Alpha to Alpha (0.1.0a1)

1. **Add version field** to all programs:
   ```json
   {
     "version": "0.1.0-alpha"
   }
   ```

2. **Update trigger syntax** (optional but recommended):
   - Old: `{"type": "afterStep", "stepId": "step-id"}`
   - New: `{"on": "step-id"}`

3. **Schema validation** now requires version field

## Roadmap

### Alpha Phase (Current)
- [x] Basic program structure
- [x] Simplified trigger syntax
- [x] Resource constraints
- [ ] Environment schemas
- [ ] Advanced validation

### Beta Phase (Planned)
- [ ] Resource specifications
- [ ] Template system
- [ ] Advanced planning algorithms
- [ ] Performance optimizations

### 1.0 Release (Planned)
- [ ] Stable API
- [ ] Complete documentation
- [ ] Migration tools
- [ ] Ecosystem tools

## Contributing

This is an alpha release. We welcome feedback and contributions, but please note that breaking changes may occur. Please:

1. Test thoroughly with your use cases
2. Report issues with detailed examples
3. Suggest improvements with concrete proposals
4. Be prepared for schema changes

## License

Apache License 2.0 