"""Redacted failed runs must not become model history."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import MethodType
from unittest.mock import patch
import unittest
from streamlit.testing.v1 import AppTest


class ChatErrorTests(unittest.TestCase):
    def test_failures_do_not_leak_or_persist_partial_answers(self):
        source = Path(__file__).resolve().parents[1] / 'app.py'
        for raises in (False, True):
            calls = []
            async def stream(self, message, history):
                calls.append(history)
                if len(calls) > 1:
                    yield {'type': 'response', 'content': 'Recovered reply'}
                    yield {'type': 'response_complete'}
                    return
                yield {'type': 'response', 'content': 'Incomplete answer'}
                if raises:
                    raise RuntimeError('Bearer private-token')
                yield {'type': 'error', 'content': 'Bearer private-token'}
            original = Path.cwd()
            with self.subTest(raises=raises), TemporaryDirectory() as tmp, patch.dict(os.environ, {'MCP_SERVER_URL': '', 'MCP_BEARER_TOKEN': ''}), patch('diagnostics.ollama_models', return_value=['qwen3:14b']):
                try:
                    os.chdir(tmp)
                    app = AppTest.from_file(str(source)).run(timeout=20)
                    client = app.session_state['app']
                    client.get_streaming_response = MethodType(stream, client)
                    app.chat_input[0].set_value('First attempt').run(timeout=20)
                    self.assertEqual(list(app.exception), [])
                    self.assertTrue(app.error)
                    self.assertFalse(any('private-token' in e.value for e in app.error))
                    self.assertEqual(app.session_state['messages'], [{'role': 'user', 'content': 'First attempt'}])
                    app.chat_input[0].set_value('Try again explicitly').run(timeout=20)
                    self.assertEqual(list(app.exception), [])
                    self.assertEqual([m.content for m in calls[-1]], ['First attempt'])
                    self.assertEqual(app.session_state['messages'][-1]['content'], 'Recovered reply')
                finally:
                    os.chdir(original)
