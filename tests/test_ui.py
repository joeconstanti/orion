"""Render and exercise the Streamlit flow with no live services."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from pydantic_ai.models.test import TestModel
from streamlit.testing.v1 import AppTest


class UITests(unittest.TestCase):
    def test_startup_and_streamed_chat(self):
        source = Path(__file__).resolve().parents[1] / 'app.py'
        original = Path.cwd()
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {'MCP_SERVER_URL': '', 'MCP_BEARER_TOKEN': ''}), patch('diagnostics.ollama_models', return_value=['qwen3:14b']), patch('pydantic_ai.models.openai.OpenAIChatModel', return_value=TestModel(custom_output_text='Hello Orion')):
            try:
                os.chdir(tmp)
                app = AppTest.from_file(str(source)).run(timeout=20)
                self.assertEqual(list(app.exception), [])
                app.chat_input[0].set_value('Hello').run(timeout=20)
                self.assertEqual(list(app.exception), [])
                self.assertEqual(app.session_state['messages'][-1]['content'], 'Hello Orion')
                self.assertTrue(any(m.value == 'Hello Orion' for m in app.markdown))
            finally:
                os.chdir(original)
