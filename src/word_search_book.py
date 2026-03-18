from __future__ import annotations

import argparse
import json
import math
import random
import string
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

INCH = 72
PAGE_SIZES = {
    "letter": (8.5 * INCH, 11 * INCH),
    "6x9": (6 * INCH, 9 * INCH),
    "8.5x11": (8.5 * INCH, 11 * INCH),
}

DIRECTIONS = (
    (1, 0),
    (-1, 0),
    (0, 1),
    (0, -1),
    (1, 1),
    (-1, -1),
    (1, -1),
    (-1, 1),
)

FONT_NAMES = {
    "regular": "Helvetica",
    "bold": "Helvetica-Bold",
    "italic": "Helvetica-Oblique",
}

PDF_FONTS = {
    "regular": "F1",
    "bold": "F2",
    "italic": "F3",
}


@dataclass(frozen=True)
class Placement:
    word: str
    start_row: int
    start_col: int
    delta_row: int
    delta_col: int

    @property
    def coordinates(self) -> list[tuple[int, int]]:
        return [
            (
                self.start_row + index * self.delta_row,
                self.start_col + index * self.delta_col,
            )
            for index in range(len(self.word))
        ]


@dataclass(frozen=True)
class Puzzle:
    title: str
    grid: list[list[str]]
    placements: list[Placement]
    words: list[str]

    def solution_cells(self) -> set[tuple[int, int]]:
        cells: set[tuple[int, int]] = set()
        for placement in self.placements:
            cells.update(placement.coordinates)
        return cells


class PuzzleGenerationError(RuntimeError):
    """Raised when a valid word-search grid cannot be produced."""


class WordSearchGenerator:
    def __init__(self, grid_size: int = 15, seed: int | None = None) -> None:
        self.grid_size = grid_size
        self.random = random.Random(seed)

    def generate(self, title: str, words: Sequence[str]) -> Puzzle:
        cleaned_words = self._clean_words(words)
        if not cleaned_words:
            raise ValueError("Each puzzle must contain at least one valid word.")
        if max(len(word) for word in cleaned_words) > self.grid_size:
            raise ValueError(
                f"A word is longer than the grid size ({self.grid_size})."
            )

        ordered_words = sorted(cleaned_words, key=len, reverse=True)
        for _ in range(250):
            grid = [[""] * self.grid_size for _ in range(self.grid_size)]
            placements: list[Placement] = []
            if self._place_words(grid, ordered_words, placements):
                self._fill_empty_cells(grid)
                return Puzzle(title=title, grid=grid, placements=placements, words=ordered_words)
        raise PuzzleGenerationError(
            f"Could not place all words for '{title}' after multiple attempts."
        )

    def _clean_words(self, words: Sequence[str]) -> list[str]:
        seen: set[str] = set()
        cleaned: list[str] = []
        for raw_word in words:
            normalized = "".join(char for char in raw_word.upper() if char in string.ascii_uppercase)
            if normalized and normalized not in seen:
                cleaned.append(normalized)
                seen.add(normalized)
        return cleaned

    def _place_words(
        self,
        grid: list[list[str]],
        words: Sequence[str],
        placements: list[Placement],
    ) -> bool:
        for word in words:
            if not self._place_single_word(grid, word, placements):
                return False
        return True

    def _place_single_word(
        self,
        grid: list[list[str]],
        word: str,
        placements: list[Placement],
    ) -> bool:
        candidates: list[Placement] = []
        for delta_row, delta_col in DIRECTIONS:
            for row in range(self.grid_size):
                for col in range(self.grid_size):
                    placement = Placement(word, row, col, delta_row, delta_col)
                    if self._can_place_word(grid, placement):
                        candidates.append(placement)
        if not candidates:
            return False

        placement = self.random.choice(candidates)
        for (row, col), letter in zip(placement.coordinates, word):
            grid[row][col] = letter
        placements.append(placement)
        return True

    def _can_place_word(self, grid: list[list[str]], placement: Placement) -> bool:
        for (row, col), letter in zip(placement.coordinates, placement.word):
            if row < 0 or row >= self.grid_size or col < 0 or col >= self.grid_size:
                return False
            existing = grid[row][col]
            if existing not in ("", letter):
                return False
        return True

    def _fill_empty_cells(self, grid: list[list[str]]) -> None:
        letters = string.ascii_uppercase
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if not grid[row][col]:
                    grid[row][col] = self.random.choice(letters)


class SimplePDF:
    def __init__(self, page_size: tuple[float, float]) -> None:
        self.page_size = page_size
        self.pages: list[str] = []

    def add_page(self, commands: Sequence[str]) -> None:
        self.pages.append("\n".join(commands))

    def save(self, output_path: Path) -> None:
        width, height = self.page_size
        objects: list[bytes] = []

        def add_object(body: bytes) -> int:
            objects.append(body)
            return len(objects)

        font_objects = {
            key: add_object(
                f"<< /Type /Font /Subtype /Type1 /BaseFont /{FONT_NAMES[key]} >>".encode("latin-1")
            )
            for key in ("regular", "bold", "italic")
        }

        page_ids: list[int] = []
        content_ids: list[int] = []
        pages_object_index = len(objects) + 1

        for page_content in self.pages:
            content_stream = page_content.encode("latin-1")
            content_id = add_object(
                b"<< /Length " + str(len(content_stream)).encode("ascii") + b" >>\nstream\n" + content_stream + b"\nendstream"
            )
            content_ids.append(content_id)
            page_id = add_object(
                (
                    f"<< /Type /Page /Parent {pages_object_index} 0 R "
                    f"/MediaBox [0 0 {width:.2f} {height:.2f}] "
                    f"/Resources << /Font << /F1 {font_objects['regular']} 0 R /F2 {font_objects['bold']} 0 R /F3 {font_objects['italic']} 0 R >> >> "
                    f"/Contents {content_id} 0 R >>"
                ).encode("latin-1")
            )
            page_ids.append(page_id)

        kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
        add_object(f"<< /Type /Pages /Count {len(page_ids)} /Kids [{kids}] >>".encode("latin-1"))
        catalog_id = add_object(f"<< /Type /Catalog /Pages {pages_object_index} 0 R >>".encode("latin-1"))

        pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for object_number, body in enumerate(objects, start=1):
            offsets.append(len(pdf))
            pdf.extend(f"{object_number} 0 obj\n".encode("ascii"))
            pdf.extend(body)
            pdf.extend(b"\nendobj\n")

        xref_start = len(pdf)
        pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        pdf.extend(
            (
                f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
                f"startxref\n{xref_start}\n%%EOF\n"
            ).encode("ascii")
        )
        output_path.write_bytes(pdf)


class PDFBookRenderer:
    def __init__(
        self,
        output_path: Path,
        page_size: tuple[float, float],
        margin: float = 0.5 * INCH,
    ) -> None:
        self.output_path = output_path
        self.page_size = page_size
        self.margin = margin
        self.width, self.height = page_size
        self.pdf = SimplePDF(page_size)

    def render(
        self,
        book_title: str,
        subtitle: str,
        author: str,
        puzzles: Sequence[Puzzle],
        include_title_page: bool = True,
        include_instructions_page: bool = True,
        include_solutions_title_page: bool = True,
    ) -> None:
        if include_title_page:
            self._draw_title_page(book_title, subtitle, author, len(puzzles))
        if include_instructions_page:
            self._draw_instructions_page()
        for index, puzzle in enumerate(puzzles, start=1):
            self._draw_puzzle_page(index, puzzle)
        if include_solutions_title_page:
            self._draw_solution_section_title()
        for index, puzzle in enumerate(puzzles, start=1):
            self._draw_solution_page(index, puzzle)
        self.pdf.save(self.output_path)

    def _draw_title_page(self, title: str, subtitle: str, author: str, puzzle_count: int) -> None:
        commands = [
            self._centered_text(title, self.height - 2.2 * INCH, 26, "bold"),
            self._centered_text(subtitle, self.height - 3.0 * INCH, 16, "regular"),
            self._centered_text(f"{puzzle_count} large-print word search puzzles", self.height - 3.8 * INCH, 13, "regular"),
            self._centered_text(f"Created by {author}", self.height - 4.3 * INCH, 13, "regular"),
            self._centered_text("Designed for Amazon KDP interiors", self.height - 5.1 * INCH, 12, "italic"),
        ]
        self.pdf.add_page(commands)

    def _draw_instructions_page(self) -> None:
        y = self.height - self.margin
        commands = [self._text(self.margin, y, "How to use this manuscript", 20, "bold")]
        y -= 0.4 * INCH
        lines = [
            "- Print-ready interior with one puzzle per page and a solution section in the back.",
            "- Keep page size and margins aligned with your Amazon KDP trim settings.",
            "- Customize book title, author name, themes, and grid size from the command line.",
            "- Review trademarked terms before publication and proof the generated PDF carefully.",
        ]
        for line in lines:
            commands.append(self._text(self.margin, y, line, 12, "regular"))
            y -= 0.32 * INCH
        self.pdf.add_page(commands)

    def _draw_solution_section_title(self) -> None:
        commands = [
            self._centered_text("Solutions", self.height - 2.0 * INCH, 24, "bold"),
            self._centered_text("Answer keys for every puzzle in the book", self.height - 2.6 * INCH, 13, "regular"),
        ]
        self.pdf.add_page(commands)

    def _draw_puzzle_page(self, number: int, puzzle: Puzzle) -> None:
        commands = [self._text(self.margin, self.height - self.margin, f"Puzzle {number}: {puzzle.title}", 18, "bold")]
        commands.extend(
            self._grid_commands(
                puzzle.grid,
                solution_cells=None,
                top=self.height - 1.7 * INCH,
                left=self.margin,
                footer_words=puzzle.words,
            )
        )
        self.pdf.add_page(commands)

    def _draw_solution_page(self, number: int, puzzle: Puzzle) -> None:
        commands = [self._text(self.margin, self.height - self.margin, f"Solution {number}: {puzzle.title}", 18, "bold")]
        commands.extend(
            self._grid_commands(
                puzzle.grid,
                solution_cells=puzzle.solution_cells(),
                top=self.height - 1.7 * INCH,
                left=self.margin,
                footer_words=puzzle.words,
            )
        )
        self.pdf.add_page(commands)

    def _grid_commands(
        self,
        grid: list[list[str]],
        solution_cells: set[tuple[int, int]] | None,
        top: float,
        left: float,
        footer_words: Sequence[str],
    ) -> list[str]:
        commands: list[str] = []
        grid_size = len(grid)
        available_width = self.width - (2 * self.margin)
        available_height = self.height - (3.7 * INCH)
        cell_size = min(available_width / grid_size, available_height / grid_size)
        grid_width = cell_size * grid_size
        grid_height = cell_size * grid_size
        start_x = left + (available_width - grid_width) / 2
        start_y = top - grid_height

        commands.append("0 0 0 RG 0.6 w")
        for row in range(grid_size + 1):
            y = start_y + row * cell_size
            commands.append(f"{start_x:.2f} {y:.2f} m {start_x + grid_width:.2f} {y:.2f} l S")
        for col in range(grid_size + 1):
            x = start_x + col * cell_size
            commands.append(f"{x:.2f} {start_y:.2f} m {x:.2f} {start_y + grid_height:.2f} l S")

        font_size = max(10, cell_size * 0.42)
        for row, letters in enumerate(grid):
            for col, letter in enumerate(letters):
                x = start_x + col * cell_size
                y = start_y + (grid_size - row - 1) * cell_size
                if solution_cells and (row, col) in solution_cells:
                    commands.append(f"0.55 0.08 0.08 rg {x + 1:.2f} {y + 1:.2f} {cell_size - 2:.2f} {cell_size - 2:.2f} re f")
                    commands.append(self._text(x + cell_size * 0.34, y + cell_size * 0.28, letter, font_size, "bold", color=(1, 1, 1)))
                else:
                    commands.append(self._text(x + cell_size * 0.34, y + cell_size * 0.28, letter, font_size, "bold"))

        commands.extend(self._word_bank_commands(footer_words, start_y - 0.45 * INCH))
        return commands

    def _word_bank_commands(self, words: Sequence[str], baseline_y: float) -> list[str]:
        commands: list[str] = []
        column_count = 2 if len(words) > 12 else 1
        col_width = (self.width - 2 * self.margin) / column_count
        rows = math.ceil(len(words) / column_count)
        for index, word in enumerate(words):
            col = index // rows
            row = index % rows
            x = self.margin + (col * col_width)
            y = baseline_y - row * 0.22 * INCH
            commands.append(self._text(x, y, f"- {word}", 11, "regular"))
        return commands

    def _centered_text(self, text: str, y: float, size: float, style: str) -> str:
        width_guess = len(text) * size * 0.52
        x = (self.width - width_guess) / 2
        return self._text(x, y, text, size, style)

    def _text(
        self,
        x: float,
        y: float,
        text: str,
        size: float,
        style: str,
        color: tuple[float, float, float] = (0, 0, 0),
    ) -> str:
        escaped = self._escape_pdf_text(text)
        r, g, b = color
        font = PDF_FONTS[style]
        return f"BT {r:.2f} {g:.2f} {b:.2f} rg /{font} {size:.2f} Tf 1 0 0 1 {x:.2f} {y:.2f} Tm ({escaped}) Tj ET"

    @staticmethod
    def _escape_pdf_text(text: str) -> str:
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def load_theme_file(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Theme file must contain a JSON list.")
    return data


def build_puzzles(theme_data: Sequence[dict[str, object]], grid_size: int, seed: int | None) -> list[Puzzle]:
    generator = WordSearchGenerator(grid_size=grid_size, seed=seed)
    puzzles: list[Puzzle] = []
    for entry in theme_data:
        title = str(entry["title"])
        words = entry["words"]
        if not isinstance(words, Iterable) or isinstance(words, (str, bytes)):
            raise ValueError(f"Words for '{title}' must be a list.")
        puzzles.append(generator.generate(title, list(words)))
    return puzzles


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a word search puzzle book PDF with solutions for Amazon KDP."
    )
    parser.add_argument("--input", type=Path, required=True, help="JSON file with puzzle themes and word lists.")
    parser.add_argument("--output", type=Path, default=Path("output/word-search-book.pdf"), help="Where to write the PDF.")
    parser.add_argument("--title", default="Word Search Puzzle Book", help="Book title for the opening page.")
    parser.add_argument("--subtitle", default="Fun themed puzzles with answer keys", help="Subtitle for the title page.")
    parser.add_argument("--author", default="Your Brand Name", help="Author name to print on the title page.")
    parser.add_argument("--grid-size", type=int, default=15, help="Grid size for each puzzle.")
    parser.add_argument("--page-size", choices=sorted(PAGE_SIZES), default="6x9", help="KDP trim size / PDF page size.")
    parser.add_argument("--margin", type=float, default=0.5, help="Margin in inches.")
    parser.add_argument("--seed", type=int, default=None, help="Optional seed for deterministic puzzles.")
    parser.add_argument("--skip-title-page", action="store_true", help="Do not add the opening title page.")
    parser.add_argument("--skip-instructions-page", action="store_true", help="Do not add the how-to page.")
    parser.add_argument("--skip-solutions-title-page", action="store_true", help="Do not add the solutions section divider page.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    theme_data = load_theme_file(args.input)
    puzzles = build_puzzles(theme_data, grid_size=args.grid_size, seed=args.seed)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    renderer = PDFBookRenderer(
        output_path=args.output,
        page_size=PAGE_SIZES[args.page_size],
        margin=args.margin * INCH,
    )
    renderer.render(
        book_title=args.title,
        subtitle=args.subtitle,
        author=args.author,
        puzzles=puzzles,
        include_title_page=not args.skip_title_page,
        include_instructions_page=not args.skip_instructions_page,
        include_solutions_title_page=not args.skip_solutions_title_page,
    )
    print(f"Created {args.output} with {len(puzzles)} puzzles and solutions.")


if __name__ == "__main__":
    main()
