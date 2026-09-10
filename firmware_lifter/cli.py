from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .config import (
    ConfigError,
    CustomTransportConfig,
    CustomTransportDetails,
    GdbTransportConfig,
    GdbTransportDetails,
    OpenOcdTransportConfig,
    OpenOcdTransportDetails,
    ResolvedProfile,
    Stm32FlashTransportConfig,
    Stm32FlashTransportDetails,
    TransportConfig,
    load_project_config,
    resolve_profile,
)
from .transports import ExecutionError, execute_profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="firmware-lifter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List available profiles")

    run_parser = subparsers.add_parser("run", help="Run a profile")
    run_parser.add_argument("profile", help="Profile name")

    upload_parser = subparsers.add_parser(
        "upload", help="Upload an image without project configuration"
    )
    upload_transports = upload_parser.add_subparsers(dest="transport", required=True)

    gdb_parser = upload_transports.add_parser("gdb", help="Upload using GDB")
    gdb_parser.add_argument("image", help="Firmware image")
    gdb_parser.add_argument("--target", required=True, help="GDB target address")
    gdb_parser.add_argument("--gdb-binary", default="gdb-multiarch")

    openocd_parser = upload_transports.add_parser(
        "openocd", help="Upload using OpenOCD"
    )
    openocd_parser.add_argument("image", help="Firmware image")
    openocd_parser.add_argument("--openocd-binary", required=True)
    openocd_parser.add_argument("--config-file", action="append", required=True)

    stm32flash_parser = upload_transports.add_parser(
        "stm32flash", help="Upload using stm32flash"
    )
    stm32flash_parser.add_argument("image", help="Firmware image")
    stm32flash_parser.add_argument("--stm32flash-binary", required=True)
    stm32flash_parser.add_argument("--device", required=True)
    stm32flash_parser.add_argument("--baudrate", type=int, required=True)

    custom_parser = upload_transports.add_parser(
        "custom", help="Upload using a custom command template"
    )
    custom_parser.add_argument("image", help="Firmware image")
    custom_parser.add_argument("--template", required=True)
    custom_parser.add_argument("--shell", default="/bin/sh")

    return parser


def resolve_standalone_profile(args: argparse.Namespace, root: Path) -> ResolvedProfile:
    transport: TransportConfig
    if args.transport == "gdb":
        transport = GdbTransportConfig(
            details=GdbTransportDetails(
                gdb_binary=args.gdb_binary,
                target=args.target,
            )
        )
    elif args.transport == "openocd":
        transport = OpenOcdTransportConfig(
            details=OpenOcdTransportDetails(
                openocd_binary=args.openocd_binary,
                config_files=args.config_file,
            )
        )
    elif args.transport == "stm32flash":
        transport = Stm32FlashTransportConfig(
            details=Stm32FlashTransportDetails(
                stm32flash_binary=args.stm32flash_binary,
                device=args.device,
                baudrate=args.baudrate,
            )
        )
    elif args.transport == "custom":
        transport = CustomTransportConfig(
            details=CustomTransportDetails(template=args.template, shell=args.shell)
        )
    else:
        raise ConfigError(f"Unsupported transport type: {args.transport}")

    return ResolvedProfile(
        name="standalone",
        image=args.image,
        pre_transfer=None,
        transport=transport,
        project_root=root,
    )


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path.cwd()

    try:
        if args.command == "list":
            project = load_project_config(root)
            for name in sorted(project.profiles):
                print(name)
            return 0

        if args.command == "run":
            profile = resolve_profile(root, args.profile)
            execute_profile(profile)
            return 0

        if args.command == "upload":
            profile = resolve_standalone_profile(args, root)
            execute_profile(profile)
            return 0
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ExecutionError as exc:
        label = "Pre-transfer" if exc.phase == "pre_transfer" else "Transfer"
        print(f"{label} failed with exit code {exc.returncode}", file=sys.stderr)
        if exc.stderr:
            sys.stderr.write(exc.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"Execution failed: {exc}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
