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

    async def test_skill_activation_through_real_agent_loop(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from pydantic_ai.models.function import FunctionModel
        from pydantic_ai.messages import ModelResponse, ToolCallPart, TextPart, ToolReturnPart
        from skills import SkillRegistry
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'sample'
            folder.mkdir()
            (folder / 'SKILL.md').write_text('---\nname: sample\ndescription: Sample task\n---\nUse source evidence.')
            app = self.make_app()
            app.skills = SkillRegistry(Path(tmp))
            app.update_system_prompt('Keep this custom prompt')
            calls = []
            def respond(messages, info):
                calls.append(messages)
                returns = [p for m in messages for p in m.parts if isinstance(p, ToolReturnPart)]
                if not returns:
                    return ModelResponse(parts=[ToolCallPart('activate_skill', {'name': 'sample'})])
                self.assertIn('Use source evidence.', returns[-1].content)
                return ModelResponse(parts=[TextPart('Skill loaded')])
            with app.agent.override(model=FunctionModel(respond)):
                self.assertEqual(await app.get_agent_response('Use sample', []), 'Skill loaded')
            self.assertEqual(len(calls), 2)
            self.assertEqual(app.system_prompt, 'Keep this custom prompt')
            app.update_settings(model_name='another')
            self.assertIn('sample', app.skills.catalog())
