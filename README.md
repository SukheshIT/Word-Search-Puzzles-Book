# Puzzles-Book

A Python tool for generating a word search puzzle book manuscript for Amazon KDP, including solution pages in the back of the book.

## Features

- Creates multiple themed word search puzzles from a JSON file.
- Exports a print-ready PDF sized for common KDP trim sizes like `6x9` and `8.5x11`.
- Adds a title page, instructions page, puzzle pages, and a full solutions section.
- Uses a deterministic random seed when you want reproducible interiors.

## Setup

Fastest option:

```bash
bash scripts/setup.sh
source .venv/bin/activate
```

Manual option:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Input format

Create a JSON array where each item contains a puzzle `title` and a list of `words`.

```json
[
  {
    "title": "Animals",
    "words": ["Elephant", "Giraffe", "Penguin", "Rabbit"]
  },
  {
    "title": "Travel",
    "words": ["Passport", "Airplane", "Compass", "Ticket"]
  }
]
```

A sample file is included at `examples/themes.json`.

## Generate the book

```bash
python src/word_search_book.py \
  --input examples/themes.json \
  --output output/word-search-book.pdf \
  --title "Large Print Word Search Puzzle Book" \
  --subtitle "A relaxing activity book with answer keys" \
  --author "Your Pen Name" \
  --grid-size 15 \
  --page-size 6x9 \
  --seed 42
```

## Command-line options

- `--input`: JSON file with puzzle themes.
- `--output`: PDF file to create.
- `--title`: Book title for the opening page.
- `--subtitle`: Subtitle shown on the title page.
- `--author`: Author or brand name.
- `--grid-size`: Grid dimensions for every puzzle.
- `--page-size`: One of `6x9`, `8.5x11`, or `letter`.
- `--margin`: Margin size in inches.
- `--seed`: Optional random seed for repeatable puzzle layouts.
- `--skip-title-page`: Omit the opening title page.
- `--skip-instructions-page`: Omit the instructions page.
- `--skip-solutions-title-page`: Omit the solutions divider page.



## Nature book example

To build a nature-themed book sized for Amazon KDP at `8.5x11`, use the included 99-puzzle input file and skip the instructions page so the final PDF totals 200 pages (99 puzzle pages + 99 solution pages + title page + solutions divider page):

```bash
python src/word_search_book.py \
  --input examples/nature_99_puzzles.json \
  --output output/nature-word-search-book.pdf \
  --title "Nature Word Search Puzzle Book" \
  --subtitle "200 pages with solutions" \
  --author "Your Pen Name" \
  --grid-size 15 \
  --page-size 8.5x11 \
  --seed 42 \
  --skip-instructions-page
```

## Verify the generated PDF

After generating the book, you can inspect the output without installing system packages:

```bash
python tools/file_info.py output/word-search-book.pdf
python - <<'PY2'
from pathlib import Path
pdf = Path('output/word-search-book.pdf')
print(pdf.exists(), pdf.stat().st_size)
print(pdf.read_bytes()[:8])
PY2
```

The local `tools/file_info.py` script reports the document type and PDF version, while the Python fallback checks that the file exists and starts with the `%PDF-1.4` header.

## Amazon KDP notes

- Match the generated PDF page size to the trim size you choose in KDP.
- Review puzzle content and word lists to avoid trademark or copyright issues.
- Proof the exported PDF before publishing to confirm margins, fonts, and page order.

## Run tests

```bash
python -m unittest discover -s tests
```
