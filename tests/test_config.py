import os
import tempfile
import unittest
from unittest.mock import patch
from hush.config import Config, DEFAULTS


class TestConfigResilience(unittest.TestCase):
    def test_stats_rounding(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_cfg_path = os.path.join(tmpdir, "config.json")
            with patch("hush.config.CONFIG_PATH", tmp_cfg_path), \
                 patch("hush.config.APP_DIR", tmpdir), \
                 patch("hush.config.MODELS_DIR", os.path.join(tmpdir, "models")):
                cfg = Config()
                cfg.add_stats(5, 1.3333333)
                cfg.add_stats(3, 2.6666667)
                stats = cfg.get("stats")
                self.assertEqual(stats["words"], 8)
                self.assertEqual(stats["utterances"], 2)
                self.assertEqual(stats["audio_seconds"], 4.0)

    def test_save_fallback_on_locked_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_cfg_path = os.path.join(tmpdir, "config.json")
            with patch("hush.config.CONFIG_PATH", tmp_cfg_path), \
                 patch("hush.config.APP_DIR", tmpdir), \
                 patch("hush.config.MODELS_DIR", os.path.join(tmpdir, "models")):
                cfg = Config()
                # Mock os.replace to simulate Windows PermissionError [WinError 32]
                with patch("os.replace", side_effect=PermissionError("Simulated WinError 32")):
                    cfg.set("strip_fillers", False)
                    # Verify fallback wrote the file directly
                    self.assertFalse(cfg.get("strip_fillers"))
                    self.assertTrue(os.path.exists(tmp_cfg_path))


if __name__ == "__main__":
    unittest.main()
