import unittest
from detector import product_names, _publisher_matches, _normalize_name

class DetectionIdentityTests(unittest.TestCase):
    def test_gemini_identity_does_not_include_drive(self):
        p={"id":"gemini","name":"Google Gemini","publisher":"Google"}
        allowed=product_names(p)
        self.assertIn(_normalize_name("Google Gemini"),allowed)
        self.assertNotIn(_normalize_name("Google Drive"),allowed)
        self.assertTrue(_publisher_matches(p,"Google LLC"))
    def test_registry_display_name_match_is_exact(self):
        allowed=product_names({"id":"chatgpt","name":"ChatGPT"})
        self.assertIn(_normalize_name("ChatGPT"),allowed)
        self.assertNotIn(_normalize_name("ChatGPT Updater"),allowed)
    def test_aliases_are_platform_scoped(self):
        gemini=product_names({"id":"gemini","name":"Google Gemini"})
        copilot=product_names({"id":"copilot","name":"Microsoft Copilot"})
        self.assertIn("gemini",gemini)
        self.assertNotIn("gemini",copilot)

if __name__=="__main__": unittest.main()
