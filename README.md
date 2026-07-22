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
- `gdb`: `target`, optional `gdb_binary` defaulting to `gdb-multiarch`
- `openocd`: `openocd_binary`, `config_files`
- `stm32flash`: `stm32flash_binary`, `device`, `baudrate`
- `custom`: `template`, optional `shell`

Custom templates support placeholders like `{{image}}`, `{{profile}}`, `{{project_root}}`, and transport detail keys.

See `examples/` for complete configurations for different transports.
The profile example file `examples/.firmware-lifter-profiles.yaml` is usable for all transports.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for developer-related documentation.


## License

This project is licensed under GNU GPL v3 or later.
See `LICENSE` for the full text.
