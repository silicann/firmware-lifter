from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from firmware_lifter.config import (
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
)
from firmware_lifter.transports import (
    build_transport_command,
    execute_profile,
    render_template,
)


class TransportTests(unittest.TestCase):
    def make_profile(self, transport: TransportConfig) -> ResolvedProfile:
        return ResolvedProfile(
            name="debug",
            image="build/debug.bin",
            pre_transfer="make build",
            transport=transport,
            project_root=Path("/project"),
        )

    def test_build_gdb_command(self) -> None:
        profile = self.make_profile(
            GdbTransportConfig(
                details=GdbTransportDetails(gdb_binary="gdb", target="localhost:3333")
            )
        )
        self.assertEqual(
            build_transport_command(profile),
            [
                "gdb",
                "--batch",
                "build/debug.bin",
                "-ex",
                "target remote localhost:3333",
                "-ex",
                "load",
            ],
        )

    def test_render_template(self) -> None:
        profile = self.make_profile(
            CustomTransportConfig(
                details=CustomTransportDetails(
                    template="flash {{image}} via {{profile}}"
                )
            )
        )
        self.assertEqual(
            render_template(profile, profile.transport.details),
            "flash build/debug.bin via debug",
        )

    def test_execute_profile_runs_pre_transfer_and_transport(self) -> None:
        profile = self.make_profile(
            Stm32FlashTransportConfig(
                details=Stm32FlashTransportDetails(
                    stm32flash_binary="stm32flash",
                    device="/dev/ttyUSB0",
                    baudrate=115200,
                ),
            )
        )

        with patch("firmware_lifter.transports.subprocess.run") as run:
            execute_profile(profile)

        self.assertEqual(run.call_count, 2)
        pre_transfer_call = run.call_args_list[0]
        transport_call = run.call_args_list[1]

        self.assertEqual(pre_transfer_call.args[0], "make build")
        self.assertEqual(pre_transfer_call.kwargs["shell"], True)
        self.assertEqual(
            transport_call.args[0],
            ["stm32flash", "-b", "115200", "-w", "build/debug.bin", "/dev/ttyUSB0"],
        )

    def test_build_openocd_command(self) -> None:
        profile = self.make_profile(
            OpenOcdTransportConfig(
                details=OpenOcdTransportDetails(
                    openocd_binary="openocd", config_files=["board.cfg", "target.cfg"]
                )
            )
        )
        self.assertEqual(
            build_transport_command(profile),
            [
                "openocd",
                "-f",
                "board.cfg",
                "-f",
                "target.cfg",
                "-c",
                "program build/debug.bin verify reset exit",
            ],
        )
