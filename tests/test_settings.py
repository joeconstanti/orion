import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from settings_store import read_settings, write_settings


class SettingsTests(unittest.TestCase):
    def test_roundtrip_private_and_empty_override(self):
        with TemporaryDirectory() as tmp:
            file = Path(tmp) / 'settings.json'
            write_settings({'mcp_url': ''}, str(file))
            self.assertEqual(read_settings(str(file), {'mcp_url': 'http://environment'}), {'mcp_url': ''})
            if os.name == 'posix':
                self.assertEqual(file.stat().st_mode & 0o777, 0o600)

    def test_replace_failure_preserves_previous_file_and_cleans_temp(self):
        with TemporaryDirectory() as tmp:
            file = Path(tmp) / 'settings.json'
            write_settings({'model': 'old'}, str(file))
            with patch('settings_store.os.replace', side_effect=OSError('Disk failure')):
                with self.assertRaises(OSError):
                    write_settings({'model': 'new'}, str(file))
            self.assertEqual(json.loads(file.read_text()), {'model': 'old'})
            self.assertEqual(list(Path(tmp).iterdir()), [file])

    def test_invalid_types_and_missing_file(self):
        with TemporaryDirectory() as tmp:
            file = Path(tmp) / 'settings.json'
            defaults = {'model': 'default'}
            self.assertEqual(read_settings(str(file), defaults), defaults)
            for content in [[], {'model': None}, {'model': 42}]:
                file.write_text(json.dumps(content))
                with self.assertRaises(ValueError):
                    read_settings(str(file), defaults)
            with self.assertRaises(ValueError):
                write_settings({'model': None}, str(file))

    def test_app_load_honors_saved_empty_mcp(self):
        from app import load_settings_from_file
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {'MCP_SERVER_URL': 'http://environment'}):
            file = Path(tmp) / 'settings.json'
            self.assertEqual(load_settings_from_file(str(file))['mcp_url'], 'http://environment')
            write_settings({'mcp_url': ''}, str(file))
            self.assertEqual(load_settings_from_file(str(file))['mcp_url'], '')
