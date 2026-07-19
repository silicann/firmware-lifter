from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import patch

from firmware_lifter.cli import main


class CliTests(unittest.TestCase):
    def write(self, root: Path, name: str, content: str) -> None:
        (root / name).write_text(content, encoding="utf-8")

    def test_run_hides_traceback_but_keeps_stderr(self) -> None:
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

            with patch("firmware_lifter.cli.Path.cwd", return_value=root), patch(
                "firmware_lifter.cli.execute_profile",
                side_effect=CalledProcessError(
                    returncode=1,
                    cmd=["gdb-multiarch"],
                    stderr="gdb: target unreachable\n",
                ),
            ), redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(["run", "debug"])

        self.assertEqual(exit_code, 1)
        self.assertIn("Execution failed with exit code 1", stderr.getvalue())
        self.assertIn("gdb: target unreachable", stderr.getvalue())
        self.assertEqual(stdout.getvalue(), "")
