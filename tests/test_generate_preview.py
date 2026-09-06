from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


preview = load_module("generate_preview_test", ROOT / "scripts" / "generate_preview.py")


class PreviewTests(unittest.TestCase):
    def test_preview_is_deterministic_png(self):
        first = preview.render()
        second = preview.render()
        self.assertEqual(first, second)
        self.assertTrue(first.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_preview_generate_and_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertTrue(preview.generate(root))
            self.assertTrue(preview.generate(root, check=True))
            path = root / preview.OUTPUT
            path.write_bytes(path.read_bytes() + b"x")
            self.assertFalse(preview.generate(root, check=True))


if __name__ == "__main__":
    unittest.main()
