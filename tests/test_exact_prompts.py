"""Custom instructions are user data, including empty strings and whitespace."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from app import PydanticAIWebApp, DEFAULT_SYSTEM_PROMPT, load_settings_from_file
from streamlit.testing.v1 import AppTest


class ExactPromptTests(unittest.TestCase):
    def test_constructor_and_updates_preserve_empty_and_whitespace(self):
        with patch('app.load_dotenv'), patch.dict(os.environ, {'MCP_SERVER_URL': '', 'MCP_BEARER_TOKEN': ''}):
            self.assertEqual(PydanticAIWebApp(system_prompt=None).system_prompt, DEFAULT_SYSTEM_PROMPT)
            for prompt in ('', '  Custom instructions\n\n', '   '):
                with self.subTest(prompt=prompt):
                    client = PydanticAIWebApp(system_prompt=prompt)
                    self.assertEqual(client.system_prompt, prompt)
                    client.update_settings(system_prompt='temporary')
                    client.update_settings(system_prompt=prompt)
                    self.assertEqual(client.system_prompt, prompt)
                    client.update_settings(model_name='another-model', system_prompt=None)
                    self.assertEqual(client.system_prompt, prompt)
                    client.update_system_prompt(prompt)
                    self.assertEqual(client.system_prompt, prompt)

    def test_editor_save_and_restart_preserve_exact_prompt(self):
        source = Path(__file__).resolve().parents[1] / 'app.py'
        for prompt in ('', '  Custom instructions\n\n', '   '):
            original = Path.cwd()
            with self.subTest(prompt=prompt), TemporaryDirectory() as tmp, patch.dict(os.environ, {'MCP_SERVER_URL': '', 'MCP_BEARER_TOKEN': ''}), patch('diagnostics.ollama_models', return_value=['qwen3:14b']):
                try:
                    os.chdir(tmp)
                    app = AppTest.from_file(str(source)).run(timeout=20)
                    app.text_area(key='system_prompt_input').set_value(prompt)
                    next(b for b in app.button if b.label == '🚀 Apply System Prompt').click().run(timeout=20)
                    self.assertEqual(list(app.exception), [])
                    self.assertEqual(app.session_state['system_prompt'], prompt)
                    self.assertEqual(app.session_state['app'].system_prompt, prompt)
                    self.assertEqual(load_settings_from_file()['system_prompt'], prompt)
                    restarted = AppTest.from_file(str(source)).run(timeout=20)
                    self.assertEqual(list(restarted.exception), [])
                    self.assertEqual(restarted.session_state['app'].system_prompt, prompt)
                    self.assertEqual(restarted.text_area(key='system_prompt_input').value, prompt)
                finally:
                    os.chdir(original)
