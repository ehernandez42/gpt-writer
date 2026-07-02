import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

const mockUseStyles = vi.fn()
const mockGenerationEditor = vi.fn()
const mockGet = vi.fn()

vi.mock('../queries/hooks/useStyles', () => ({
  useStyles: () => mockUseStyles(),
}))

vi.mock('../components/GenerationEditor', () => ({
  GenerationEditor: ({ content }: { content: string }) => {
    mockGenerationEditor(content)
    return <div data-testid="generation-editor">{content}</div>
  },
}))

vi.mock('../lib/api', () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    patch: vi.fn(),
  },
}))

vi.mock('../components/GeneratorForm', () => ({
  GeneratorForm: ({ onGenerated }: { onGenerated?: (generation: { id: string; generated_text: string }) => void }) => (
    <button
      type="button"
      onClick={() => onGenerated?.({ id: 'gen-1', generated_text: 'Generated from callback' })}
    >
      Trigger generation
    </button>
  ),
}))

import { GeneratePage } from './GeneratePage'

describe('GeneratePage', () => {
  it('renders the TipTap editor after a successful generation', async () => {
    mockUseStyles.mockReturnValue({ data: [], error: null })
    mockGet.mockResolvedValue([])
    const user = userEvent.setup()

    render(<GeneratePage />)

    expect(screen.queryByTestId('generation-editor')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Trigger generation' }))

    expect(screen.getByTestId('generation-editor')).toHaveTextContent('Generated from callback')
    expect(mockGenerationEditor).toHaveBeenCalledWith('Generated from callback')
  })
})
