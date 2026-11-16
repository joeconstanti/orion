import unittest
from unittest.mock import patch
from pydantic_ai.models.test import TestModel
from app import PydanticAIWebApp


class AgentTests(unittest.IsolatedAsyncioTestCase):
    def make_app(self):
        with patch.dict('os.environ', {}, clear=True), patch('app.load_dotenv'):
            return PydanticAIWebApp()

    async def test_offline_response(self):
        app = self.make_app()
        with app.agent.override(model=TestModel(custom_output_text='Hello')):
            self.assertEqual(await app.get_agent_response('Hi', []), 'Hello')

    async def test_offline_stream(self):
        app = self.make_app()
        with app.agent.override(model=TestModel(custom_output_text='Hello world')):
            chunks = [c async for c in app.get_streaming_response('Hi', [])]
        self.assertFalse(any(c['type'] == 'error' for c in chunks), chunks)
        self.assertTrue(any(c['type'] == 'response_complete' for c in chunks))
        self.assertIn('Hello', ''.join(c['content'] for c in chunks if c['type'] == 'response'))

    def test_agent_rebuild(self):
        app = self.make_app()
        app.update_system_prompt('Custom instructions')
        app.update_settings(model_name='other-model')
        self.assertEqual(app.model_name, 'other-model')
        self.assertEqual(app.system_prompt, 'Custom instructions')
