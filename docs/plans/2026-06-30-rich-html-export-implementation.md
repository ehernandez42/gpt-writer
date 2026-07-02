# Rich HTML Export Implementation Plan

> **REQUIRED SUB-SKILL:** Use the executing-plans skill to implement this plan task-by-task.

**Goal:** Preserve TipTap formatting in both PDF and DOCX export by sending editor HTML to the backend and rendering supported rich content there.

**Architecture:** The frontend export action will send HTML plus an explicit content type instead of plain text. The backend will parse a constrained subset of editor HTML into a shared intermediate document model, then render that model to PDF with ReportLab Platypus and to DOCX with `python-docx` so both formats preserve the same structure and formatting.

**Tech Stack:** React, TipTap, Vitest, FastAPI, ReportLab Platypus, python-docx, Python stdlib `html.parser`, pytest

---

### Task 1: Frontend export sends HTML

**Files:**
- Modify: `frontend/src/components/GenerationEditor.tsx`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/components/GenerationEditor.test.tsx`

**Step 1: Write the failing test**

Add a test in `frontend/src/components/GenerationEditor.test.tsx` that verifies export uses HTML instead of plain text.

```tsx
it('exports html content to the backend', async () => {
  const exportMock = vi.fn().mockResolvedValue(new Blob())
  vi.mocked(api.export).mockImplementation(exportMock)
  mockEditor.getHTML.mockReturnValue('<p><strong>Hello</strong></p>')

  const user = userEvent.setup()
  render(<GenerationEditor content="<p>Hello</p>" onChange={vi.fn()} saveStatus="idle" />)

  await user.click(screen.getByRole('button', { name: 'Export PDF' }))

  expect(exportMock).toHaveBeenCalledWith(
    '<p><strong>Hello</strong></p>',
    'pdf',
    'html',
  )
})
```

**Step 2: Run test to verify it fails**

Run: `npm test -- GenerationEditor.test.tsx`
Expected: FAIL because `handleExport` currently calls `editor.getText()` and `api.export` does not accept `content_type`.

**Step 3: Write minimal implementation**

Update `frontend/src/components/GenerationEditor.tsx`:

```tsx
async function handleExport(format: 'pdf' | 'docx') {
  const blob = await api.export(editor?.getHTML() || '', format, 'html')
  downloadBlob(blob, format === 'pdf' ? 'generated.pdf' : 'generated.docx')
}
```

Update `frontend/src/lib/api.ts`:

```ts
async export(content: string, format: 'pdf' | 'docx', contentType: 'html'): Promise<Blob> {
  const url = `${API_BASE}/export`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, format, content_type: contentType }),
  })

  if (!response.ok) throw new APIError(response.status, await response.text())
  return response.blob()
}
```

**Step 4: Run test to verify it passes**

Run: `npm test -- GenerationEditor.test.tsx`
Expected: PASS.

**Step 5: Commit**

```bash
git add frontend/src/components/GenerationEditor.tsx frontend/src/lib/api.ts frontend/src/components/GenerationEditor.test.tsx
git commit -m "feat: send html content for export"
```

### Task 2: Backend export API accepts HTML payload

**Files:**
- Modify: `backend/routers/export.py`
- Create: `backend/tests/test_export_api.py`

**Step 1: Write the failing test**

Create `backend/tests/test_export_api.py` with a request-shape test:

```python
from fastapi.testclient import TestClient
import main


def test_export_accepts_html_content_payload(monkeypatch):
    client = TestClient(main.app)

    monkeypatch.setattr(
        'routers.export.export_document',
        lambda content, format, content_type: {
            'filename': 'generated.pdf',
            'content_type': 'application/pdf',
            'content': b'pdf-bytes',
        },
    )

    response = client.post('/export', json={
        'content': '<p>Hello</p>',
        'format': 'pdf',
        'content_type': 'html',
    })

    assert response.status_code == 200
    assert response.headers['content-type'].startswith('application/pdf')
```

**Step 2: Run test to verify it fails**

Run: `pytest -q backend/tests/test_export_api.py`
Expected: FAIL because `ExportRequest` currently expects `text`, and router still calls `export_text`.

**Step 3: Write minimal implementation**

Update `backend/routers/export.py`:

```python
from services.export import export_document

class ExportRequest(BaseModel):
    content: str
    format: str
    content_type: str

@router.post('/export')
def export_endpoint(payload: ExportRequest):
    try:
        file_data = export_document(payload.content, payload.format, payload.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    ...
```

**Step 4: Run test to verify it passes**

Run: `pytest -q backend/tests/test_export_api.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add backend/routers/export.py backend/tests/test_export_api.py
git commit -m "feat: accept html export payloads"
```

### Task 3: Shared HTML parser and model

**Files:**
- Modify: `backend/services/export.py`
- Create: `backend/tests/test_export_parser.py`

**Step 1: Write the failing test**

Create `backend/tests/test_export_parser.py` that proves supported HTML becomes a structured document model.

```python
from services.export import parse_html_document


def test_parse_html_document_preserves_supported_blocks_and_marks():
    document = parse_html_document(
        '<h1 style="text-align:center">Title</h1>'
        '<p><strong>Bold</strong> and <em>italic</em> text.</p>'
        '<ul><li>One</li><li>Two</li></ul>'
        '<blockquote><u>Quoted</u></blockquote>'
        '<hr>'
    )

    assert document[0].type == 'heading'
    assert document[0].level == 1
    assert document[0].align == 'center'
    assert document[1].inlines[0].bold is True
    assert document[1].inlines[1].italic is True
    assert document[2].ordered is False
    assert document[3].type == 'blockquote'
    assert document[4].type == 'horizontal_rule'
```

**Step 2: Run test to verify it fails**

Run: `pytest -q backend/tests/test_export_parser.py`
Expected: FAIL because no parser/model exists.

**Step 3: Write minimal implementation**

In `backend/services/export.py`, add small dataclasses and a constrained parser.

```python
from dataclasses import dataclass, field
from html.parser import HTMLParser

@dataclass
class TextRun:
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False

@dataclass
class Block:
    type: str
    inlines: list[TextRun] = field(default_factory=list)
    level: int | None = None
    align: str = 'left'
    ordered: bool | None = None
    items: list[list[TextRun]] = field(default_factory=list)

# implement parse_html_document(html: str) -> list[Block]
```

Support only tags you need: `h1`, `h2`, `p`, `strong`, `b`, `em`, `i`, `u`, `ul`, `ol`, `li`, `blockquote`, `hr`, `br`. Unsupported tags should degrade to text.

**Step 4: Run test to verify it passes**

Run: `pytest -q backend/tests/test_export_parser.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add backend/services/export.py backend/tests/test_export_parser.py
git commit -m "feat: parse export html into document model"
```

### Task 4: PDF renderer with wrapping and formatting

**Files:**
- Modify: `backend/services/export.py`
- Create: `backend/tests/test_export_pdf.py`

**Step 1: Write the failing test**

Create `backend/tests/test_export_pdf.py`:

```python
from services.export import export_document


def test_pdf_export_supports_rich_html_without_truncation():
    html = (
        '<h1>Heading</h1>'
        '<p><strong>Bold</strong> paragraph with enough text to require wrapping. ' * 20 + '</p>'
        '<ul><li>First item</li><li>Second item</li></ul>'
    )

    result = export_document(html, 'pdf', 'html')

    assert result['filename'] == 'generated.pdf'
    assert result['content_type'] == 'application/pdf'
    assert len(result['content']) > 1000
```

**Step 2: Run test to verify it fails**

Run: `pytest -q backend/tests/test_export_pdf.py`
Expected: FAIL because exporter still uses `drawString` or no PDF renderer exists yet.

**Step 3: Write minimal implementation**

Implement a Platypus renderer in `backend/services/export.py`:

```python
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

# build flowables from parsed blocks
# use SimpleDocTemplate(buffer, leftMargin=0.75*inch, rightMargin=0.75*inch, topMargin=0.75*inch, bottomMargin=0.75*inch)
```

Map inline runs to ReportLab inline markup (`<b>`, `<i>`, `<u>`). Map alignments to paragraph styles. Use `Spacer` between blocks.

**Step 4: Run test to verify it passes**

Run: `pytest -q backend/tests/test_export_pdf.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add backend/services/export.py backend/tests/test_export_pdf.py
git commit -m "feat: render html export to pdf"
```

### Task 5: DOCX renderer with matching structure

**Files:**
- Modify: `backend/services/export.py`
- Create: `backend/tests/test_export_docx.py`

**Step 1: Write the failing test**

Create `backend/tests/test_export_docx.py`:

```python
from io import BytesIO
from docx import Document
from services.export import export_document


def test_docx_export_preserves_heading_runs_and_lists():
    html = (
        '<h1>Heading</h1>'
        '<p><strong>Bold</strong> and <em>italic</em></p>'
        '<ol><li>One</li><li>Two</li></ol>'
        '<blockquote style="text-align:right"><u>Quote</u></blockquote>'
    )

    result = export_document(html, 'docx', 'html')
    document = Document(BytesIO(result['content']))

    assert document.paragraphs[0].text == 'Heading'
    assert document.paragraphs[0].style.name.startswith('Heading')
    assert any(run.bold for run in document.paragraphs[1].runs)
    assert any(run.italic for run in document.paragraphs[1].runs)
```

**Step 2: Run test to verify it fails**

Run: `pytest -q backend/tests/test_export_docx.py`
Expected: FAIL because DOCX export currently uses a single plain paragraph.

**Step 3: Write minimal implementation**

Extend `backend/services/export.py` with a DOCX renderer using the same parsed model.

```python
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches

# add paragraph per block
# add runs per inline node
# set run.bold / run.italic / run.underline
# set paragraph alignment
# indent blockquotes
# use heading styles for heading blocks
```

For list blocks, create one paragraph per item using list-compatible paragraph styles such as `'List Bullet'` and `'List Number'`.

**Step 4: Run test to verify it passes**

Run: `pytest -q backend/tests/test_export_docx.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add backend/services/export.py backend/tests/test_export_docx.py
git commit -m "feat: render html export to docx"
```

### Task 6: Unified export dispatcher and regression coverage

**Files:**
- Modify: `backend/services/export.py`
- Modify: `backend/tests/test_export_api.py`
- Modify: `frontend/src/components/GenerationEditor.test.tsx`

**Step 1: Write the failing test**

Add a regression test ensuring unsupported `content_type` returns a clear validation error.

```python
def test_export_rejects_unsupported_content_type(client):
    response = client.post('/export', json={
        'content': 'plain text',
        'format': 'pdf',
        'content_type': 'text',
    })

    assert response.status_code == 400
    assert 'Unsupported content type' in response.text
```

**Step 2: Run test to verify it fails**

Run: `pytest -q backend/tests/test_export_api.py`
Expected: FAIL until dispatcher validates `content_type`.

**Step 3: Write minimal implementation**

In `backend/services/export.py`, add a single public entry point:

```python
def export_document(content: str, format: str, content_type: str) -> dict:
    if content_type != 'html':
        raise ValueError('Unsupported content type')

    document = parse_html_document(content)
    if format == 'pdf':
        return export_pdf_document(document)
    if format == 'docx':
        return export_docx_document(document)
    raise ValueError('Unsupported export format')
```

**Step 4: Run test to verify it passes**

Run: `pytest -q backend/tests/test_export_api.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add backend/services/export.py backend/tests/test_export_api.py frontend/src/components/GenerationEditor.test.tsx
git commit -m "feat: finalize html export pipeline"
```

### Task 7: End-to-end verification

**Files:**
- Verify existing touched files only.

**Step 1: Run backend tests**

Run: `cd backend && pytest -q`
Expected: all backend tests pass.

**Step 2: Run frontend tests**

Run: `cd frontend && npm test`
Expected: all frontend tests pass.

**Step 3: Run the applications manually**

Run backend:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

Run frontend:
```bash
cd frontend
npm run dev
```

**Step 4: Verify PDF export manually**
- Create or open a generation.
- Apply headings, bold, italic, underline, lists, blockquote, alignment, and horizontal rule.
- Export PDF.
- Confirm wrapping stays on-page and formatting is materially preserved.

**Step 5: Verify DOCX export manually**
- Export the same document as DOCX.
- Open in Word or LibreOffice.
- Confirm headings, inline marks, lists, blockquotes, alignment, and horizontal rule are preserved as expected.

**Step 6: Commit**

```bash
git add backend frontend docs/plans/2026-06-30-rich-html-export-design.md docs/plans/2026-06-30-rich-html-export-implementation.md
git commit -m "feat: add rich html export for pdf and docx"
```
