# Past Generated Writing Editing Implementation Plan

> **REQUIRED SUB-SKILL:** Use the executing-plans skill to implement this plan task-by-task.

**Goal:** Let users reopen past generations on the Generate page, edit the original generation directly, and auto-save changes.

**Architecture:** Extend the backend `generations` resource with list and patch operations and store `updated_at` on generation records. Refactor the Generate page to own the selected generation, load generation history, render the shared TipTap editor, and debounce auto-save of editor changes back to the existing generation row.

**Tech Stack:** FastAPI, sqlite3, React, React Query, TipTap, Vitest, pytest

---

### Task 1: Backend generations API

**Files:**
- Modify: `backend/database/init.sql`
- Modify: `backend/services/generate.py`
- Modify: `backend/routers/generate.py`
- Create: `backend/tests/test_generations.py`

**Step 1: Write the failing tests**
- Add a backend test for `GET /generations` returning recent generations.
- Add a backend test for `PATCH /generations/{id}` updating `generated_text` and `updated_at`.

**Step 2: Run test to verify it fails**
- Run: `pytest -q backend/tests/test_generations.py`
- Expected: FAIL because route/service behavior does not exist yet.

**Step 3: Write minimal implementation**
- Add `updated_at` to `generations` schema.
- Update generation creation to populate `updated_at`.
- Add service functions to list and update generations.
- Add `GET /generations` and `PATCH /generations/{id}` routes.

**Step 4: Run test to verify it passes**
- Run: `pytest -q backend/tests/test_generations.py`
- Expected: PASS.

### Task 2: Frontend generation history and autosave tests

**Files:**
- Create: `frontend/src/routes/GeneratePage.history.test.tsx`
- Modify: `frontend/src/components/GenerationEditor.test.tsx`
- Modify: `frontend/src/components/GeneratorForm.tsx` (only after tests exist)
- Modify: `frontend/src/routes/GeneratePage.tsx` (only after tests exist)

**Step 1: Write the failing tests**
- Add a page test for rendering past generations and selecting one to load into the editor.
- Add a page/editor test for debounced autosave and visible save state.

**Step 2: Run test to verify it fails**
- Run: `npm test -- GeneratePage.history.test.tsx GenerationEditor.test.tsx`
- Expected: FAIL because history/autosave behavior does not exist yet.

**Step 3: Write minimal implementation**
- Add frontend API helpers for listing and patching generations.
- Make Generate page fetch history, track selected generation, track save state, and pass selected content into the editor.
- Keep GeneratorForm focused on generation creation and pass full generated object back up.

**Step 4: Run test to verify it passes**
- Run: `npm test -- GeneratePage.history.test.tsx GenerationEditor.test.tsx`
- Expected: PASS.

### Task 3: Editor integration

**Files:**
- Modify: `frontend/src/components/GenerationEditor.tsx`
- Modify: `frontend/src/styles.css`

**Step 1: Write the failing test**
- Extend editor test to verify editor content updates when selection changes and emits content changes upward.

**Step 2: Run test to verify it fails**
- Run: `npm test -- GenerationEditor.test.tsx`
- Expected: FAIL because editor is currently self-contained.

**Step 3: Write minimal implementation**
- Convert editor to controlled-ish integration: accept current content, notify on content changes, render save status, and keep export bound to current editor text.

**Step 4: Run test to verify it passes**
- Run: `npm test -- GenerationEditor.test.tsx`
- Expected: PASS.

### Task 4: End-to-end verification

**Files:**
- Verify existing touched files only.

**Step 1: Run backend tests**
- Run: `pytest -q`

**Step 2: Run frontend tests**
- Run: `npm test`

**Step 3: Run the app manually**
- Backend: `uvicorn main:app --reload --port 8000`
- Frontend: `npm run dev`
- Verify: generate content, see it appear in history, reopen an older generation, edit it, observe auto-save status, refresh and confirm persisted edits remain.
