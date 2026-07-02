# Rich HTML Export Design

**Goal:** Preserve TipTap formatting in both PDF and DOCX export using backend-generated documents from editor HTML.

## Summary

The current export path loses formatting because the frontend sends plain text and the backend renders that text with a trivial single-line PDF implementation and a one-paragraph DOCX implementation. The new design makes editor HTML the canonical export input. The frontend sends HTML from TipTap, the backend parses that HTML into a constrained intermediate document model, and both PDF and DOCX renderers consume that shared model.

## Architecture

### Frontend
- `GenerationEditor` exports `editor.getHTML()` instead of `editor.getText()`.
- Export payload becomes HTML-aware, e.g. `{ content, format, content_type: "html" }`.
- Frontend tests verify that export uses HTML.

### Backend
- `/export` accepts HTML content.
- Export service parses supported HTML tags into an intermediate representation.
- PDF renderer uses ReportLab Platypus flowables for wrapping and pagination.
- DOCX renderer uses `python-docx` paragraphs/runs/alignment from the same model.

## Supported v1 Formatting
- headings
- bold
- italic
- underline
- paragraphs
- bullet lists
- numbered lists
- blockquotes
- alignment
- horizontal rules

Unsupported tags should degrade gracefully to paragraph text.

## Intermediate Document Model
Suggested block nodes:
- `Heading(level, align, inlines)`
- `Paragraph(align, inlines)`
- `ListBlock(ordered, items)`
- `Blockquote(align, inlines)`
- `HorizontalRule()`

Suggested inline nodes:
- `TextRun(text, bold=False, italic=False, underline=False)`

This shared representation keeps PDF and DOCX output aligned and prevents duplicate HTML parsing logic.

## Implementation Slices
1. Frontend export sends HTML and adds regression test.
2. Backend export API accepts HTML and gets failing tests for rich export cases.
3. Shared HTML parser builds constrained document model.
4. PDF renderer implemented with Platypus.
5. DOCX renderer implemented with `python-docx`.
6. End-to-end verification with real editor-generated HTML.

## Verification
- Frontend test confirms HTML export payload.
- Backend tests verify export generation from HTML snippets.
- Manual verification confirms wrapping, paragraph spacing, headings, lists, alignment, and preserved formatting in both PDF and DOCX.
