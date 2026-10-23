import unittest
import numpy as np
from hush.audio import Recorder


class TestRecorderBuffer(unittest.TestCase):
    def test_read_range_slice(self):
        rec = Recorder()
        rec._capturing = True
        # Simulate 10 chunks of 1600 samples each (total 16,000 samples)
        for i in range(10):
            chunk = np.full(1600, float(i), dtype=np.float32)
            rec._chunks.append(chunk)
            rec._samples += len(chunk)

        # Request samples from index 1600 to 3200 (should equal chunk 1, all 1.0s)
        sliced = rec.read_range(1600, 3200)
        self.assertEqual(len(sliced), 1600)
        np.testing.assert_array_equal(sliced, np.full(1600, 1.0, dtype=np.float32))

        # Request spanning chunks: samples 1000 to 2000 (600 from chunk 0, 400 from chunk 1)
        spanning = rec.read_range(1000, 2000)
        self.assertEqual(len(spanning), 1000)
        self.assertEqual(spanning[0], 0.0)
        self.assertEqual(spanning[599], 0.0)
        self.assertEqual(spanning[600], 1.0)
        self.assertEqual(spanning[999], 1.0)

    def test_callback_exception_safety(self):
        def bad_on_level(level):
            raise RuntimeError("Simulated websocket disconnect")

        rec = Recorder(on_level=bad_on_level)
        rec._capturing = True
        fake_data = np.ones((1600, 1), dtype=np.float32)
        # Calling _callback must not propagate exceptions to PortAudio
        try:
            rec._callback(fake_data, 1600, None, 0)
        except Exception as e:
            self.fail(f"_callback raised an unhandled exception: {e}")
        self.assertEqual(rec.sample_count, 1600)


if __name__ == "__main__":
    unittest.main()
