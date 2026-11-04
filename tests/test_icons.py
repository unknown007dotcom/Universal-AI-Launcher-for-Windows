import unittest
from pathlib import Path

class IconAssetTests(unittest.TestCase):
    def test_every_builtin_platform_has_a_local_png_logo(self):
        ids=["chatgpt","gemini","claude","deepseek","perplexity","copilot","grok","poe","meta-ai","arena","huggingchat","mistral"]
        for platform_id in ids:
            with self.subTest(platform=platform_id):
                path=Path(__file__).resolve().parents[1]/"assets"/"icons"/(platform_id+".png")
                self.assertTrue(path.is_file(),str(path))
                self.assertTrue(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"),str(path))

if __name__=="__main__": unittest.main()
