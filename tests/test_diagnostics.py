import unittest
import httpx
from diagnostics import ollama_models, validate_service_url


class DiagnosticsTests(unittest.TestCase):
    def test_model_list(self):
        def handler(request):
            self.assertEqual(str(request.url), 'http://localhost:11434/api/tags')
            return httpx.Response(200, json={'models': [{'name': 'qwen3:14b'}, {}, None]})
        self.assertEqual(ollama_models('http://localhost:11434/', transport=httpx.MockTransport(handler)), ['qwen3:14b'])

    def test_malformed_and_failed_responses(self):
        for response in [httpx.Response(200, json=[]), httpx.Response(503)]:
            with self.subTest(status=response.status_code), self.assertRaises((ValueError, httpx.HTTPStatusError)):
                ollama_models('http://localhost', transport=httpx.MockTransport(lambda _: response))

    def test_reject_credential_urls(self):
        for url in ['file:///etc/passwd', 'https://user:secret@host', 'http://host?token=secret', 'http://host:bad']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_service_url(url)
