# firmware-lifter

Semi-automated firmware transfer to a target device.

## Usage

Place these files in your project root:

`.firmware-lifter-profiles.yaml`
```yaml
profiles:
  debug:
    image: build/debug.bin
    pre_transfer: make build-debug
  release:
    image: build/release.bin
```

`.firmware-lifter-transport.yaml`
```yaml
transport:
  type: gdb
  details:
    gdb_binary: arm-none-eabi-gdb
    target: localhost:3333
```

Run `firmware-lifter list` to show available profiles and `firmware-lifter run debug` to execute one.

Supported transports:
- `gdb`: `gdb_binary`, `target`
- `openocd`: `openocd_binary`, `config_files`
- `stm32flash`: `stm32flash_binary`, `device`, `baudrate`
- `custom`: `template`, optional `shell`

Custom templates support placeholders like `{{image}}`, `{{profile}}`, `{{project_root}}`, and transport detail keys.

See `examples/` for complete configurations for different transports.
The profile example file `examples/.firmware-lifter-profiles.yaml` is usable for all transports.

## Development

firmware-lifter uses [`hatch`](https://hatch.pypa.io/) and the `pyproject.toml` to organise the project.

Dependencies are listed in the `pyproject.toml` and will be installed upon running python commands within the virtual environment created by `hatch`.

## Linting & formatting

`firmware-lifter` provides a preconfigured `hatch` action (see `pyproject.toml`) for
typing checks:
- `hatch run style:typing` for type check with `mypy`

By default hatch provides
[static analysis checks](https://hatch.pypa.io/dev/config/internal/static-analysis/) via the `fmt`
action:
- `hatch fmt --check` for linting (defaults to `ruff`)
- `hatch fmt` for formatting (defaults to `ruff`)


Code coverage can be checked with `hatch test --cover`. Note, [coverage](https://coverage.readthedocs.io/en/7.12.0/#) should be available on the machine before running coverage analysis.

## Versioning

firmware-lifter use [`bump-my-version`](https://github.com/callowayproject/bump-my-version) for versioning.
- `hatch version major|minor|patch` will increase the respective level.
