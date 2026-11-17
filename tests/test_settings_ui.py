"""Saving failures must preserve the active configuration and chat."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from settings_store import write_settings
from streamlit.testing.v1 import AppTest


class SettingsUITests(unittest.TestCase):
    def test_failed_apply_prompt_and_reset_preserve_state_then_retry(self):
        source = Path(__file__).resolve().parents[1] / 'app.py'
        for action in ('settings', 'prompt', 'reset'):
            original = Path.cwd()
            with self.subTest(action=action), TemporaryDirectory() as tmp, patch.dict(os.environ, {'MCP_SERVER_URL': '', 'MCP_BEARER_TOKEN': ''}), patch('diagnostics.ollama_models', return_value=['qwen3:14b']):
                try:
                    os.chdir(tmp)
                    write_settings({'system_prompt': 'Original instructions'}, 'orion_settings.json')
                    before_file = Path('orion_settings.json').read_bytes()
                    app = AppTest.from_file(str(source)).run(timeout=20)
                    client = app.session_state['app']
                    messages = [{'role': 'user', 'content': 'Keep my chat'}]
                    app.session_state['messages'] = messages.copy()
                    if action == 'settings':
                        app.text_input(key='mcp_token_input').set_value('example-new-token')
                        button = next(b for b in app.button if b.key == 'apply_settings_btn')
                    elif action == 'prompt':
                        app.text_area(key='system_prompt_input').set_value('New instructions')
                        button = next(b for b in app.button if b.label == '🚀 Apply System Prompt')
                    else:
                        button = next(b for b in app.button if b.label == '🔄 Reset')
                    with patch('settings_store.os.replace', side_effect=OSError('private filesystem details')):
                        button.click().run(timeout=20)
                    self.assertEqual(list(app.exception), [])
                    self.assertTrue(any('Failed to save settings' in e.value for e in app.error))
                    self.assertFalse(any('saved' in e.value for e in app.success))
                    self.assertEqual(app.session_state['system_prompt'], 'Original instructions')
                    self.assertEqual(client.system_prompt, 'Original instructions')
                    self.assertEqual(app.session_state['mcp_token'], '')
                    self.assertEqual(client.mcp_token, '')
                    self.assertEqual(app.session_state['messages'], messages)
                    self.assertEqual(Path('orion_settings.json').read_bytes(), before_file)
                    # Draft widgets remain available for a deliberate retry.
                    button = next(b for b in app.button if b.label == button.label)
                    button.click().run(timeout=20)
                    self.assertEqual(list(app.exception), [])
                    saved = json.loads(Path('orion_settings.json').read_text())
                    if action == 'settings':
                        self.assertEqual(saved['mcp_token'], 'example-new-token')
                        self.assertEqual(client.mcp_token, 'example-new-token')
                    else:
                        self.assertNotEqual(saved['system_prompt'], 'Original instructions')
                        self.assertEqual(client.system_prompt, saved['system_prompt'])
                        self.assertEqual(app.session_state['messages'], [])
                finally:
                    os.chdir(original)
