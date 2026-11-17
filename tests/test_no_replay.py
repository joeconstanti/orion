"""A submitted chat must never automatically replay tools."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from streamlit.testing.v1 import AppTest


class NoReplayTests(unittest.TestCase):
    def test_short_empty_thinking_and_failed_streams_never_replay(self):
        source = Path(__file__).resolve().parents[1] / 'app.py'
        for chunks in (
            [{'type': 'response', 'content': 'OK'}, {'type': 'response_complete'}],
            [{'type': 'response_complete'}],
            [{'type': 'thinking', 'content': 'considering'}, {'type': 'response_complete'}],
            [{'type': 'error', 'content': 'Request failed'}],
        ):
            calls = []
            async def stream(self, message, history):
                calls.append(message)
                for chunk in chunks:
                    yield chunk
            original = Path.cwd()
            with self.subTest(chunks=chunks), TemporaryDirectory() as tmp, patch.dict(os.environ, {'MCP_SERVER_URL': '', 'MCP_BEARER_TOKEN': ''}), patch('diagnostics.ollama_models', return_value=['qwen3:14b']):
                try:
                    os.chdir(tmp)
                    app = AppTest.from_file(str(source)).run(timeout=20)
                    from types import MethodType
                    client = app.session_state['app']
                    client.get_streaming_response = MethodType(stream, client)
                    with patch.object(client, 'get_agent_response', side_effect=AssertionError('Automatic replay')) as fallback:
                        app.chat_input[0].set_value('Do this once').run(timeout=20)
                        fallback.assert_not_called()
                    self.assertEqual(list(app.exception), [])
                    self.assertEqual(calls, ['Do this once'])
                    if chunks[0].get('content') == 'OK':
                        self.assertEqual(app.session_state['messages'][-1]['content'], 'OK')
                finally:
                    os.chdir(original)
