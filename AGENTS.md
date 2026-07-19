# AGENTS.md

## Project
`firmware-lifter` is a small CLI for project-local firmware transfer operations.

## Working Rules
- Keep changes minimal and focused.
- Prefer `apply_patch` for edits.
- Do not use destructive git commands.
- Preserve existing repo conventions unless a change is required.
- Keep ASCII unless the file already uses Unicode.

## Architecture Notes
- YAML config is split into:
  - `.firmware-lifter-profiles.yaml` for project-shared profile data
  - `.firmware-lifter-transport.yaml` for local transport data
- YAML parsing uses `ruamel.yaml`.
- Validation uses strict `pydantic v2` models.
- One local transport applies to all profiles.
- Supported transports:
  - `gdb`
  - `openocd`
  - `stm32flash`
  - `custom`

## Execution Behavior
- `pre_transfer` runs before transport execution.
- Execution failures should not show Python tracebacks.
- Backend stderr must remain visible.
- Distinguish `pre_transfer` failures from transfer failures in CLI output.

## Examples
- Example configs live in `examples/`.
- The shared profile example file is `examples/.firmware-lifter-profiles.yaml`.
- Transport-specific examples live in transport subdirectories.

## Testing
- Prefer updating existing tests in place.
- Run tests with `hatch test` when available.
- If hatch is unavailable, use the local venv pytest path when present.
- A quick syntax check can be done with:
  - `python3 -m compileall firmware_lifter tests`

## Code Quality
- Keep command construction explicit and readable.
- Validate config early and fail with clear messages.
- Avoid adding compatibility layers unless there is a concrete need.
