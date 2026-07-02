import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

let capturedOnUpdate: ((payload: { editor: { getHTML: () => string } }) => void) | undefined

const run = vi.fn()
const commandChain = {
  focus: vi.fn(() => commandChain),
  toggleBold: vi.fn(() => commandChain),
  toggleHeading: vi.fn(() => commandChain),
  setParagraph: vi.fn(() => commandChain),
  toggleItalic: vi.fn(() => commandChain),
  toggleUnderline: vi.fn(() => commandChain),
  toggleCode: vi.fn(() => commandChain),
  toggleBulletList: vi.fn(() => commandChain),
  toggleOrderedList: vi.fn(() => commandChain),
  toggleBlockquote: vi.fn(() => commandChain),
  setTextAlign: vi.fn(() => commandChain),
  setHorizontalRule: vi.fn(() => commandChain),
  undo: vi.fn(() => commandChain),
  redo: vi.fn(() => commandChain),
  run,
}
const chain = vi.fn(() => commandChain)

const mockEditor = {
  chain,
  isActive: vi.fn(() => false),
  getText: vi.fn(() => 'Edited text'),
  getHTML: vi.fn(() => '<p>Edited text</p>'),
  commands: {
    setContent: vi.fn(),
  },
}

vi.mock('@tiptap/react', () => ({
  EditorContent: () => <div data-testid="editor-content" />,
  useEditor: (options?: { onUpdate?: (payload: { editor: { getHTML: () => string } }) => void }) => {
    capturedOnUpdate = options?.onUpdate
    return mockEditor
  },
}))

vi.mock('../lib/api', () => ({
  api: {
    export: vi.fn(),
  },
}))

import { api } from '../lib/api'
import { GenerationEditor } from './GenerationEditor'

describe('GenerationEditor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockEditor.getHTML.mockReturnValue('<p>Edited text</p>')
    mockEditor.getText.mockReturnValue('Edited text')
    vi.mocked(api.export).mockResolvedValue(new Blob())
    vi.stubGlobal('URL', {
      createObjectURL: vi.fn(() => 'blob:mock-url'),
      revokeObjectURL: vi.fn(),
    })
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('renders icon toolbar buttons with accessible labels and applies bold', async () => {
    const user = userEvent.setup()

    render(<GenerationEditor content="Hello world" onChange={vi.fn()} saveStatus="saved" />)

    expect(screen.getByRole('button', { name: 'Paragraph' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Bold' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Underline' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Align center' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Undo' })).toBeInTheDocument()
    expect(screen.getByText('Saved')).toBeInTheDocument()
    expect(screen.queryByText('Bold')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Bold' }))

    expect(chain).toHaveBeenCalled()
    expect(commandChain.focus).toHaveBeenCalled()
    expect(commandChain.toggleBold).toHaveBeenCalled()
    expect(run).toHaveBeenCalled()
  })

  it('syncs incoming content into the editor instance', () => {
    const { rerender } = render(
      <GenerationEditor content="First version" onChange={vi.fn()} saveStatus="idle" />,
    )

    rerender(<GenerationEditor content="Second version" onChange={vi.fn()} saveStatus="idle" />)

    expect(mockEditor.commands.setContent).toHaveBeenCalledWith('Second version', false)
  })

  it('emits html content changes so formatting-only edits can be saved', () => {
    const onChange = vi.fn()
    render(<GenerationEditor content="<p>Hello</p>" onChange={onChange} saveStatus="idle" />)

    capturedOnUpdate?.({
      editor: {
        getHTML: () => '<p><strong>Hello</strong></p>',
      },
    })

    expect(onChange).toHaveBeenCalledWith('<p><strong>Hello</strong></p>')
  })

  it('exports html content to the backend', async () => {
    const exportMock = vi.fn().mockResolvedValue(new Blob())
    vi.mocked(api.export).mockImplementation(exportMock)
    mockEditor.getHTML.mockReturnValue('<p><strong>Hello</strong></p>')

    const user = userEvent.setup()
    render(<GenerationEditor content="<p>Hello</p>" onChange={vi.fn()} saveStatus="idle" />)

    await user.click(screen.getByRole('button', { name: 'Export PDF' }))
    await user.click(screen.getByRole('button', { name: 'Export DOCX' }))

    expect(exportMock).toHaveBeenNthCalledWith(
      1,
      '<p><strong>Hello</strong></p>',
      'pdf',
      'html',
    )
    expect(exportMock).toHaveBeenNthCalledWith(
      2,
      '<p><strong>Hello</strong></p>',
      'docx',
      'html',
    )
  })
})
