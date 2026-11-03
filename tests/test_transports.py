from __future__ import annotations

import subprocess
import tempfile
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
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temporary_directory.name)
        image = self.project_root / "build" / "debug.bin"
        image.parent.mkdir()
        image.touch()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def make_profile(self, transport: TransportConfig) -> ResolvedProfile:
        return ResolvedProfile(
            name="debug",
            image="build/debug.bin",
            pre_transfer="make build",
            transport=transport,
            project_root=self.project_root,
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
                "-ex",
                "monitor reset halt",
                "-ex",
                "target extended-remote localhost:3333",
                "-ex",
                "load",
                "-ex",
                "compare-sections",
                "-ex",
                "monitor reset run",
                "build/debug.bin",
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

    def test_gdb_mass_erase_command(self) -> None:
        profile = self.make_profile(
            GdbTransportConfig(
                details=GdbTransportDetails(
                    gdb_binary="gdb",
                    target="localhost:3333",
                    mass_erase_command="stm32f4x mass_erase 0",
                )
            )
        )

        with patch("firmware_lifter.transports.subprocess.run") as run:
            execute_profile(profile)

        self.assertEqual(
            run.call_args_list[1].args[0],
            [
                "gdb",
                "--batch",
                "-ex",
                "target extended-remote localhost:3333",
                "-ex",
                "monitor reset halt",
                "-ex",
                "monitor stm32f4x mass_erase 0",
            ],
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
        self.assertEqual(pre_transfer_call.kwargs["stderr"], subprocess.PIPE)
        self.assertEqual(pre_transfer_call.kwargs["text"], True)
        self.assertEqual(
            transport_call.args[0],
            ["stm32flash", "-b", "115200", "-w", "build/debug.bin", "/dev/ttyUSB0"],
        )
        self.assertEqual(transport_call.kwargs["stderr"], subprocess.PIPE)
        self.assertEqual(transport_call.kwargs["text"], True)

    def test_pre_transfer_can_create_image(self) -> None:
        image = self.project_root / "build" / "generated.bin"
        profile = ResolvedProfile(
            name="debug",
            image="build/generated.bin",
            pre_transfer="make build",
            transport=GdbTransportConfig(
                details=GdbTransportDetails(gdb_binary="gdb", target="localhost:3333")
            ),
            project_root=self.project_root,
        )

        def run(command, **kwargs) -> None:
            if command == "make build":
                image.touch()

        with patch(
            "firmware_lifter.transports.subprocess.run", side_effect=run
        ) as run_mock:
            execute_profile(profile)

        self.assertTrue(image.is_file())
        self.assertEqual(run_mock.call_count, 2)

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

    def test_execute_profile_runs_mass_erase_before_upload(self) -> None:
        profile = self.make_profile(
            OpenOcdTransportConfig(
                details=OpenOcdTransportDetails(
                    openocd_binary="openocd",
                    config_files=["board.cfg"],
                    mass_erase_command="stm32f4x mass_erase 0",
                )
            )
        )

        with patch("firmware_lifter.transports.subprocess.run") as run:
            execute_profile(profile)

        self.assertEqual(run.call_count, 3)
        self.assertEqual(
            run.call_args_list[1].args[0],
            [
                "openocd",
                "-f",
                "board.cfg",
                "-c",
                "init; stm32f4x mass_erase 0; shutdown",
            ],
        )
        self.assertEqual(
            run.call_args_list[2].args[0],
            [
                "openocd",
                "-f",
                "board.cfg",
                "-c",
                "program build/debug.bin verify reset exit",
            ],
        )

    def test_stm32flash_mass_erase_command(self) -> None:
        profile = self.make_profile(
            Stm32FlashTransportConfig(
                details=Stm32FlashTransportDetails(
                    stm32flash_binary="stm32flash",
                    device="/dev/ttyUSB0",
                    baudrate=115200,
                    mass_erase=True,
                )
            )
        )

        with patch("firmware_lifter.transports.subprocess.run") as run:
            execute_profile(profile)

        self.assertEqual(
            run.call_args_list[1].args[0],
            ["stm32flash", "-b", "115200", "-e", "/dev/ttyUSB0"],
        )
