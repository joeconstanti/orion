"""Discovery belongs to a server, including empty results."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from streamlit.testing.v1 import AppTest


class ModelCacheUITests(unittest.TestCase):
    def test_server_changes_refresh_options_without_applying_draft(self):
        source = Path(__file__).resolve().parents[1] / 'app.py'
        def discover(url):
            return ['other-model'] if url == 'http://other:11434' else ['qwen3:14b']
        original = Path.cwd()
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {'MCP_SERVER_URL': '', 'MCP_BEARER_TOKEN': ''}), patch('diagnostics.ollama_models', side_effect=discover) as discovery:
            try:
                os.chdir(tmp)
                app = AppTest.from_file(str(source)).run(timeout=20)
                self.assertEqual(app.selectbox(key='ollama_model_input').options, ['qwen3:14b'])
                app.text_input(key='ollama_url_input').set_value('http://other:11434').run(timeout=20)
                self.assertEqual(list(app.exception), [])
                self.assertEqual(app.selectbox(key='ollama_model_input').options, ['other-model'])
                self.assertEqual(app.session_state['app'].ollama_url, 'http://localhost:11434')
                self.assertEqual([c.args[0] for c in discovery.call_args_list].count('http://other:11434'), 1)
                app.run(timeout=20)
                self.assertEqual([c.args[0] for c in discovery.call_args_list].count('http://other:11434'), 1)
                app.button(key='refresh_models_btn').click().run(timeout=20)
                self.assertEqual([c.args[0] for c in discovery.call_args_list].count('http://other:11434'), 2)
            finally:
                os.chdir(original)

    def test_empty_discovery_is_cached_until_explicit_refresh(self):
        source = Path(__file__).resolve().parents[1] / 'app.py'
        original = Path.cwd()
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {'MCP_SERVER_URL': '', 'MCP_BEARER_TOKEN': ''}), patch('diagnostics.ollama_models', return_value=[]) as discovery:
            try:
                os.chdir(tmp)
                app = AppTest.from_file(str(source)).run(timeout=20)
                initial = discovery.call_count
                app.run(timeout=20)
                self.assertEqual(discovery.call_count, initial)
                self.assertEqual(app.text_input(key='ollama_model_input_fallback').value, 'qwen3:14b')
                app.text_input(key='ollama_model_input_fallback').set_value('manual-model:latest').run(timeout=20)
                self.assertEqual(discovery.call_count, initial)
                app.button(key='refresh_models_btn').click().run(timeout=20)
                self.assertEqual(app.text_input(key='ollama_model_input_fallback').value, 'manual-model:latest')
                self.assertEqual(discovery.call_count, initial + 1)
                self.assertEqual(list(app.exception), [])
            finally:
                os.chdir(original)
