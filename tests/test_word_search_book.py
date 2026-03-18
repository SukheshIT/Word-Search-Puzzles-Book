import tempfile
import unittest
from pathlib import Path

from src.word_search_book import PAGE_SIZES, PDFBookRenderer, WordSearchGenerator, build_puzzles


class WordSearchGeneratorTests(unittest.TestCase):
    def test_generate_places_all_requested_words(self) -> None:
        generator = WordSearchGenerator(grid_size=12, seed=7)
        puzzle = generator.generate(
            "Ocean",
            ["coral", "dolphin", "whale", "anchor", "reef"],
        )

        self.assertEqual(len(puzzle.placements), 5)
        self.assertEqual(set(puzzle.words), {"CORAL", "DOLPHIN", "WHALE", "ANCHOR", "REEF"})

        for placement in puzzle.placements:
            letters = "".join(puzzle.grid[row][col] for row, col in placement.coordinates)
            self.assertEqual(letters, placement.word)

    def test_build_puzzles_uses_theme_payload(self) -> None:
        puzzles = build_puzzles(
            [
                {"title": "Colors", "words": ["amber", "indigo", "violet"]},
                {"title": "Shapes", "words": ["circle", "square", "triangle"]},
            ],
            grid_size=10,
            seed=11,
        )

        self.assertEqual([p.title for p in puzzles], ["Colors", "Shapes"])
        self.assertTrue(all(len(p.grid) == 10 for p in puzzles))

    def test_renderer_can_skip_front_matter_for_exact_page_targets(self) -> None:
        generator = WordSearchGenerator(grid_size=10, seed=5)
        puzzles = [
            generator.generate("Nature One", ["forest", "river", "valley"]),
            generator.generate("Nature Two", ["meadow", "willow", "breeze"]),
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "custom.pdf"
            renderer = PDFBookRenderer(output_path=output_path, page_size=PAGE_SIZES["8.5x11"])
            renderer.render(
                book_title="Nature",
                subtitle="Test",
                author="Tester",
                puzzles=puzzles,
                include_title_page=True,
                include_instructions_page=False,
                include_solutions_title_page=True,
            )

            pdf_bytes = output_path.read_bytes()
            self.assertEqual(pdf_bytes.count(b"/Type /Page "), 6)


if __name__ == "__main__":
    unittest.main()
