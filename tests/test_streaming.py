import unittest
from streaming import split_output


class StreamingTests(unittest.TestCase):
    def test_plain_text_is_response(self):
        self.assertEqual(split_output('Let me think about the answer'), ('', 'Let me think about the answer'))

    def test_fragmented_tags(self):
        self.assertEqual(split_output('<thi'), ('', ''))
        self.assertEqual(split_output('<think>reason</thi'), ('reason', ''))
        self.assertEqual(split_output('<think>reason</think>answer'), ('reason', 'answer'))

    def test_unicode_before_fragmented_mixed_case_closing_tag(self):
        self.assertEqual(split_output('<ThInK>İstanbul</tHi'), ('İstanbul', ''))
        self.assertEqual(split_output('<ThInK>İstanbul</tHiNk>'), ('İstanbul', ''))
        self.assertEqual(split_output('<ThInK>İstanbul</tHiNk>answer'), ('İstanbul', 'answer'))

    def test_final_partial_text_is_preserved(self):
        self.assertEqual(split_output('<thi', final=True), ('', '<thi'))
