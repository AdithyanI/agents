---
name: pdf
description: Read, create, or review PDFs when page layout and rendering matter. Use for PDF generation, extraction, and visual verification of deliverable pages.
---

# PDF

Use text extraction for content and rendered pages for layout. `pdfplumber` and `pypdf` are useful for extraction; `reportlab` is available for programmatic creation. Choose the tool that fits the document instead of rebuilding an existing workflow.

Render pages with Poppler when visual verification matters:

```bash
pdftoppm -png <input.pdf> <output-prefix>
```

Inspect affected pages of the final version for clipping, overlaps, broken tables, missing glyphs, and legibility. Text extraction alone does not establish visual correctness. If rendering is unavailable, use another available renderer or state the validation limit.

Keep intermediates in repo `tmp/pdfs/` and remove disposable files when done. Put deliverables in the user-requested or repo-approved artifact location. In Dobby workspaces, follow the body map and artifact contract rather than creating a top-level `output/` directory.
