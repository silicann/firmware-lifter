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

### Standalone Uploads

Upload an image without project configuration using `firmware-lifter upload`:

```sh
firmware-lifter upload gdb firmware.elf --target localhost:3333
firmware-lifter upload openocd firmware.bin --openocd-binary openocd --config-file board.cfg --config-file target.cfg
firmware-lifter upload stm32flash firmware.bin --stm32flash-binary stm32flash --device /dev/ttyUSB0 --baudrate 115200 --mass-erase
firmware-lifter upload custom firmware.bin --template 'my-flasher --image "{{image}}"'
```

`gdb` accepts optional `--gdb-binary` (default: `gdb-multiarch`), and `custom` accepts optional `--shell` (default: `/bin/sh`). Custom templates support the placeholders listed below; the standalone profile name is `standalone`.

To mass erase through GDB, specify the target server's monitor command. It is sent after connecting and halting the target, before the upload:

```sh
firmware-lifter upload gdb firmware.elf --target localhost:3333 --mass-erase-command 'stm32f4x mass_erase 0'
```

To mass erase with OpenOCD, specify the target's erase command. It is run as `init; COMMAND; shutdown` before the upload:

```sh
firmware-lifter upload openocd firmware.bin --openocd-binary openocd --config-file board.cfg --mass-erase-command 'stm32f4x mass_erase 0'
```

For configuration-driven uploads, set `mass_erase: true` in `stm32flash` transport details, or set `mass_erase_command` to the target-specific GDB or OpenOCD command.

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
