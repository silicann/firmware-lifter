from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from firmware_lifter.config import (
    ConfigError,
    load_project_config,
    load_transport_config,
    resolve_profile,
)


class ConfigTests(unittest.TestCase):
    def write(self, root: Path, name: str, content: str) -> None:
        (root / name).write_text(content, encoding="utf-8")

    def test_load_and_resolve_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(
                root,
                ".firmware-lifter-profiles.yaml",
                """
profiles:
  debug:
    image: build/debug.bin
    pre_transfer: make build-debug
  release:
    image: build/release.bin
""",
            )
            self.write(
                root,
                ".firmware-lifter-transport.yaml",
                """
transport:
  type: gdb
  details:
    gdb_binary: arm-none-eabi-gdb
    target: localhost:3333
""",
            )

            project = load_project_config(root)
            self.assertEqual(sorted(project.profiles), ["debug", "release"])

            transport = load_transport_config(root)
            self.assertEqual(transport.type, "gdb")

            resolved = resolve_profile(root, "debug")
            self.assertEqual(resolved.image, "build/debug.bin")
            self.assertEqual(resolved.pre_transfer, "make build-debug")
            self.assertEqual(resolved.transport.type, "gdb")

    def test_unknown_profile_raises(self) -> None:
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
                "transport:\n  type: custom\n  details:\n    template: echo {{image}}\n",
            )

            with self.assertRaises(ConfigError):
                resolve_profile(root, "missing")

    def test_invalid_transport_type_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(
                root,
                ".firmware-lifter-transport.yaml",
                "transport:\n  type: nope\n  details: {}\n",
            )

            with self.assertRaises(ConfigError):
                load_transport_config(root)

    def test_extra_fields_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(
                root,
                ".firmware-lifter-profiles.yaml",
                "profiles:\n  debug:\n    image: build/debug.bin\n    extra: nope\n",
            )
            self.write(
                root,
                ".firmware-lifter-transport.yaml",
                "transport:\n  type: custom\n  details:\n    template: echo {{image}}\n",
            )

            with self.assertRaises(ConfigError):
                load_project_config(root)
