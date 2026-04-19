from __future__ import annotations

import unittest

from pressor.core.errors import infer_error_details


class ErrorInferenceTests(unittest.TestCase):
    def test_lossy_input_maps_to_guardrail_code(self) -> None:
        details = infer_error_details('probe', 'Rejected lossy input: codec opus is lossy', input_is_lossy=True)
        self.assertEqual(details['error_code'], 'P1501')
        self.assertEqual(details['error_category'], 'user_config')

    def test_invalid_argument_maps_to_encode_failure(self) -> None:
        details = infer_error_details('encode', 'ffmpeg failed', stderr='Invalid argument')
        self.assertEqual(details['error_code'], 'P1301')
        self.assertEqual(details['error_category'], 'runtime_processing')


if __name__ == '__main__':
    unittest.main()
