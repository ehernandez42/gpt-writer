import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const mockUseStyles = vi.fn()
const mockGet = vi.fn()
const mockPatch = vi.fn()

vi.mock('../queries/hooks/useStyles', () => ({
  useStyles: () => mockUseStyles(),
}))

vi.mock('../lib/api', () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    patch: (...args: unknown[]) => mockPatch(...args),
  },
}))

vi.mock('../components/GeneratorForm', () => ({
  GeneratorForm: ({ onGenerated }: { onGenerated?: (generation: any) => void }) => (
    <button
      type="button"
      onClick={() =>
        onGenerated?.({
          id: 'gen-3',
          style_id: 'style-1',
          prompt: 'Newest prompt',
          generated_text: 'Newest text',
          provider_used: 'ollama',
          created_at: '2026-06-30T12:00:00+00:00',
          updated_at: '2026-06-30T12:00:00+00:00',
        })
      }
    >
      Mock generate
    </button>
  ),
}))

vi.mock('../components/GenerationEditor', () => ({
  GenerationEditor: ({ content, onChange, saveStatus }: { content: string; onChange: (value: string) => void; saveStatus: string }) => (
    <div>
      <div data-testid="editor-content">{content}</div>
      <div data-testid="save-status">{saveStatus}</div>
      <button type="button" onClick={() => onChange('Edited history text')}>
        Change content
      </button>
    </div>
  ),
}))

import { GeneratePage } from './GeneratePage'

describe('GeneratePage history', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    mockUseStyles.mockReturnValue({ data: [], error: null })
    mockGet.mockResolvedValue([
      {
        id: 'gen-2',
        style_id: 'style-1',
        prompt: 'Later prompt',
        generated_text: 'Later text',
        provider_used: 'ollama',
        created_at: '2026-06-30T11:00:00+00:00',
        updated_at: '2026-06-30T11:00:00+00:00',
      },
      {
        id: 'gen-1',
        style_id: 'style-1',
        prompt: 'Earlier prompt',
        generated_text: 'Earlier text',
        provider_used: 'ollama',
        created_at: '2026-06-30T10:00:00+00:00',
        updated_at: '2026-06-30T10:00:00+00:00',
      },
    ])
    mockPatch.mockResolvedValue({
      id: 'gen-1',
      style_id: 'style-1',
      prompt: 'Earlier prompt',
      generated_text: 'Edited history text',
      provider_used: 'ollama',
      created_at: '2026-06-30T10:00:00+00:00',
      updated_at: '2026-06-30T10:05:00+00:00',
    })
  })

  afterEach(() => {
    vi.runOnlyPendingTimers()
    vi.useRealTimers()
  })

  it('loads history, selects a past generation, and autosaves edits', async () => {
    render(<GeneratePage />)

    await act(async () => {
      await Promise.resolve()
    })

    expect(screen.getByRole('button', { name: /Earlier prompt/i })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /Earlier prompt/i }))
    expect(screen.getByTestId('editor-content')).toHaveTextContent('Earlier text')

    fireEvent.click(screen.getByRole('button', { name: 'Change content' }))
    expect(screen.getByTestId('save-status')).toHaveTextContent('saving')

    await act(async () => {
      vi.advanceTimersByTime(800)
      await Promise.resolve()
      await Promise.resolve()
    })

    expect(mockPatch).toHaveBeenCalledWith('/generations/gen-1', {
      generated_text: 'Edited history text',
    })
    expect(screen.getByTestId('save-status')).toHaveTextContent('saved')
  })
})
