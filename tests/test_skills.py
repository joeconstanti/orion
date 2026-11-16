from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from skills import SkillRegistry, MAX_BYTES


class SkillTests(unittest.TestCase):
    def test_catalog_and_activation(self):
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / "example"
            folder.mkdir()
            (folder / "SKILL.md").write_text('---\nname: example\ndescription: "Task: research---evidence"\n---\nUnique body')
            registry = SkillRegistry(Path(tmp))
            self.assertIn("example", registry.catalog())
            self.assertNotIn("Unique body", registry.catalog())
            self.assertEqual(json.loads(registry.activate("example"))["instructions"], "Unique body")
            self.assertIn("Unknown skill", registry.activate("../secret"))

    def test_invalid_and_oversized_skills_are_skipped(self):
        with TemporaryDirectory() as tmp:
            for name, content in [("bad", "---\nname: [oops]\n---\ntext"), ("large", "x" * (MAX_BYTES + 1))]:
                folder = Path(tmp) / name
                folder.mkdir()
                (folder / "SKILL.md").write_text(content)
            registry = SkillRegistry(Path(tmp))
            self.assertEqual(registry.skills, {})
            self.assertEqual(len(registry.diagnostics), 2)

    def test_symlink_is_not_loaded(self):
        with TemporaryDirectory() as tmp, TemporaryDirectory() as outside:
            (Path(outside) / "SKILL.md").write_text("secret")
            (Path(tmp) / "outside").symlink_to(outside)
            self.assertEqual(SkillRegistry(Path(tmp)).skills, {})

    def test_absent_root_is_empty(self):
        self.assertEqual(SkillRegistry(Path("/missing-orion-skills")).catalog(), "")
