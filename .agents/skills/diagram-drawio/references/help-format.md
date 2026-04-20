# --help Convention

Every user-invocable skill must include a `## Help` section in its SKILL.md. When the user passes `--help` as a flag, display this section and stop without executing any workflow phases.

## Required Help Structure

```markdown
## Help

### Parameters

| Parameter | Required | Default | Description |
|---|---|---|---|
| `<primary-arg>` | yes | -- | Description of primary argument |
| `--flag` | no | default | Description of flag |

### Behavior Variations

| Input | Behavior |
|---|---|
| Condition A | What happens |
| Condition B | What happens |

### Examples

```
/skill-name arg1 --flag value
/skill-name --help
/skill-name --check
```
```

## Universal Flags

Every user-invocable skill automatically supports these flags in addition to skill-specific parameters:

| Flag | Description |
|---|---|
| `--help` | Display the Help section and stop |
| `--check` | Run preflight dependency checks only (CLI tools, MCP servers) and report status without executing any workflow |
| `--verbosity` | Output detail level: `short`, `standard`, `detailed` |

## Detection Rules

- If the user's input contains `--help`, display the **Help** section verbatim and stop. Do not run preflight, do not load references, do not execute any phase.
- If the user's input contains `--check`, run `python3 ${CLAUDE_SKILL_DIR}/scripts/preflight.py ${CLAUDE_SKILL_DIR}` and display the result. Do not load references or execute any phase.
