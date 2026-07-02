import StarterKit from '@tiptap/starter-kit'
import TextAlign from '@tiptap/extension-text-align'
import Underline from '@tiptap/extension-underline'
import { EditorContent, useEditor } from '@tiptap/react'
import {
  AlignCenter,
  AlignLeft,
  AlignRight,
  Bold,
  Code,
  Heading1,
  Heading2,
  Italic,
  List,
  ListOrdered,
  Minus,
  Pilcrow,
  Quote,
  Redo,
  Underline as UnderlineIcon,
  Undo,
} from 'lucide-react'
import { useEffect } from 'react'

import { api } from '../lib/api'

type GenerationEditorProps = {
  content: string
  onChange: (value: string) => void
  saveStatus: 'idle' | 'saving' | 'saved' | 'error'
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export function GenerationEditor({ content, onChange, saveStatus }: GenerationEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
    ],
    content,
    onUpdate: ({ editor: currentEditor }) => {
      onChange(currentEditor.getHTML())
    },
  })

  useEffect(() => {
    if (editor && editor.getHTML() !== content) {
      editor.commands.setContent(content, false)
    }
  }, [content, editor])

  async function handleExport(format: 'pdf' | 'docx') {
    const blob = await api.export(editor?.getHTML() || '', format, 'html')
    downloadBlob(blob, format === 'pdf' ? 'generated.pdf' : 'generated.docx')
  }

  const toolbarButtons = [
    { label: 'Paragraph', icon: Pilcrow, onClick: () => editor?.chain().focus().setParagraph().run(), active: editor?.isActive('paragraph') },
    { label: 'Heading 1', icon: Heading1, onClick: () => editor?.chain().focus().toggleHeading({ level: 1 }).run(), active: editor?.isActive('heading', { level: 1 }) },
    { label: 'Heading 2', icon: Heading2, onClick: () => editor?.chain().focus().toggleHeading({ level: 2 }).run(), active: editor?.isActive('heading', { level: 2 }) },
    { label: 'Bold', icon: Bold, onClick: () => editor?.chain().focus().toggleBold().run(), active: editor?.isActive('bold') },
    { label: 'Italic', icon: Italic, onClick: () => editor?.chain().focus().toggleItalic().run(), active: editor?.isActive('italic') },
    { label: 'Underline', icon: UnderlineIcon, onClick: () => editor?.chain().focus().toggleUnderline().run(), active: editor?.isActive('underline') },
    { label: 'Code', icon: Code, onClick: () => editor?.chain().focus().toggleCode().run(), active: editor?.isActive('code') },
    { label: 'Bullet List', icon: List, onClick: () => editor?.chain().focus().toggleBulletList().run(), active: editor?.isActive('bulletList') },
    { label: 'Numbered List', icon: ListOrdered, onClick: () => editor?.chain().focus().toggleOrderedList().run(), active: editor?.isActive('orderedList') },
    { label: 'Quote', icon: Quote, onClick: () => editor?.chain().focus().toggleBlockquote().run(), active: editor?.isActive('blockquote') },
    { label: 'Align left', icon: AlignLeft, onClick: () => editor?.chain().focus().setTextAlign('left').run(), active: editor?.isActive({ textAlign: 'left' }) },
    { label: 'Align center', icon: AlignCenter, onClick: () => editor?.chain().focus().setTextAlign('center').run(), active: editor?.isActive({ textAlign: 'center' }) },
    { label: 'Align right', icon: AlignRight, onClick: () => editor?.chain().focus().setTextAlign('right').run(), active: editor?.isActive({ textAlign: 'right' }) },
    { label: 'Horizontal rule', icon: Minus, onClick: () => editor?.chain().focus().setHorizontalRule().run(), active: false },
    { label: 'Undo', icon: Undo, onClick: () => editor?.chain().focus().undo().run(), active: false },
    { label: 'Redo', icon: Redo, onClick: () => editor?.chain().focus().redo().run(), active: false },
  ]

  return (
    <div className="editor-shell">
      <div className="editor-toolbar" aria-label="Editor toolbar">
        {toolbarButtons.map((button) => {
          const Icon = button.icon

          return (
            <button
              key={button.label}
              type="button"
              className={button.active ? 'is-active' : undefined}
              onClick={button.onClick}
              aria-label={button.label}
              title={button.label}
            >
              <Icon size={16} aria-hidden="true" />
            </button>
          )
        })}
      </div>
      <EditorContent editor={editor} />
      <div className="editor-status" aria-live="polite">
        {saveStatus === 'saving' ? 'Saving...' : null}
        {saveStatus === 'saved' ? 'Saved' : null}
        {saveStatus === 'error' ? 'Save failed' : null}
      </div>
      <div className="editor-actions">
        <button type="button" onClick={() => void handleExport('pdf')}>
          Export PDF
        </button>
        <button type="button" onClick={() => void handleExport('docx')}>
          Export DOCX
        </button>
      </div>
    </div>
  )
}
