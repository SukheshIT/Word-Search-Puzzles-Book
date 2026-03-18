import tempfile
import unittest
from pathlib import Path

from tools.file_info import describe_file


class FileInfoTests(unittest.TestCase):
    def test_describe_pdf_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "sample.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\nexample")

            description = describe_file(pdf_path)

            self.assertIn("PDF document, version 1.4", description)
            self.assertIn("sample.pdf", description)

    def test_describe_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_path = Path(tmp_dir) / "sample.json"
            json_path.write_text('{"hello": "world"}', encoding="utf-8")

            description = describe_file(json_path)

            self.assertIn("JSON text data", description)


if __name__ == "__main__":
    unittest.main()
