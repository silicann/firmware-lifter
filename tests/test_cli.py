from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from firmware_lifter.cli import main
from firmware_lifter.transports import ExecutionError


class CliTests(unittest.TestCase):
    def write(self, root: Path, name: str, content: str) -> None:
        (root / name).write_text(content, encoding="utf-8")

    def test_run_hides_traceback_but_keeps_stderr(self) -> None:
        cases = [
            ("transfer", "Transfer failed with exit code 1"),
            ("pre_transfer", "Pre-transfer failed with exit code 2"),
        ]

        for phase, expected in cases:
            with self.subTest(phase=phase):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    self.write(
                        root,
                        ".firmware-lifter-profiles.yaml",
                        "profiles:\n  debug:\n    image: build/debug.bin\n",
                    )
                    self.write(
                        root,
                        ".firmware-lifter-transport.yaml",
                        """
transport:
  type: gdb
  details:
    target: localhost:3333
""",
                    )

                    stderr = StringIO()
                    stdout = StringIO()

                    with patch(
                        "firmware_lifter.cli.Path.cwd", return_value=root
                    ), patch(
                        "firmware_lifter.cli.execute_profile",
                        side_effect=ExecutionError(
                            phase=phase,
                            returncode=1 if phase == "transfer" else 2,
                            stderr="gdb: target unreachable\n",
                        ),
                    ), redirect_stdout(stdout), redirect_stderr(stderr):
                        exit_code = main(["run", "debug"])

                self.assertEqual(exit_code, 1)
                self.assertIn(expected, stderr.getvalue())
                self.assertIn("gdb: target unreachable", stderr.getvalue())
                self.assertEqual(stdout.getvalue(), "")

    def test_upload_builds_standalone_profiles(self) -> None:
        cases = [
            (
                ["upload", "gdb", "firmware.elf", "--target", "localhost:3333"],
                "gdb",
                {"gdb_binary": "gdb-multiarch", "target": "localhost:3333"},
            ),
            (
                [
                    "upload",
                    "openocd",
                    "firmware.bin",
                    "--openocd-binary",
                    "openocd",
                    "--config-file",
                    "board.cfg",
                    "--config-file",
                    "target.cfg",
                ],
                "openocd",
                {
                    "openocd_binary": "openocd",
                    "config_files": ["board.cfg", "target.cfg"],
                },
            ),
            (
                [
                    "upload",
                    "stm32flash",
                    "firmware.bin",
                    "--stm32flash-binary",
                    "stm32flash",
                    "--device",
                    "/dev/ttyUSB0",
                    "--baudrate",
                    "115200",
                ],
                "stm32flash",
                {
                    "stm32flash_binary": "stm32flash",
                    "device": "/dev/ttyUSB0",
                    "baudrate": 115200,
                },
            ),
            (
                [
                    "upload",
                    "custom",
                    "firmware.bin",
                    "--template",
                    "flash {{image}}",
                    "--shell",
                    "/bin/bash",
                ],
                "custom",
                {"template": "flash {{image}}", "shell": "/bin/bash"},
            ),
        ]

        for argv, transport_type, details in cases:
            with self.subTest(transport=transport_type):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    with patch(
                        "firmware_lifter.cli.Path.cwd", return_value=root
                    ), patch("firmware_lifter.cli.execute_profile") as execute:
                        exit_code = main(argv)

                self.assertEqual(exit_code, 0)
                profile = execute.call_args.args[0]
                self.assertEqual(profile.name, "standalone")
                self.assertEqual(profile.image, argv[2])
                self.assertIsNone(profile.pre_transfer)
                self.assertEqual(profile.project_root, root)
                self.assertEqual(profile.transport.type, transport_type)
                self.assertEqual(profile.transport.details.model_dump(), details)
