import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from config_manager import ConfigManager, default_config
from detector import detect, WEB_ONLY, DETECTION_REQUIRED
from launcher import launch

class CoreTests(unittest.TestCase):
    def test_defaults_and_persistence(self):
        with tempfile.TemporaryDirectory() as d:
            c=ConfigManager(Path(d)/"config.json")
            self.assertEqual(len(c.data["platforms"]),12)
            item=c.add_platform({"id":"test","name":"Test","url":"https://example.com"})
            c.record_launch(item["id"])
            loaded=ConfigManager(c.path)
            self.assertEqual(loaded.data["platforms"][-1]["name"],"Test")
            self.assertEqual(loaded.data["recent"][0],"test")
    def test_import_rejects_invalid(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad.json"; p.write_text('{"platforms": "bad"}')
            c=ConfigManager(Path(d)/"cfg.json")
            with self.assertRaises(ValueError): c.import_from(p)
    def test_missing_configured_path_requires_detection(self):
        state,exe,_=detect({"executable":"/definitely/not/here.exe","auto_detect":True})
        self.assertEqual(state,DETECTION_REQUIRED); self.assertIsNone(exe)
    def test_unverified_auto_detection_does_not_guess(self):
        with patch("detector.os.name","posix"):
            state,exe,_=detect({"auto_detect":True})
        self.assertEqual(state,WEB_ONLY); self.assertIsNone(exe)
    def test_web_fallback_only_once(self):
        p={"url":"https://example.com","auto_detect":True,"preference":"WEB FIRST"}
        with patch("launcher.open_website",return_value=True) as web:
            self.assertEqual(launch(p,"APP FIRST")[1],"WEB")
            web.assert_called_once_with(p)

if __name__=="__main__": unittest.main()
