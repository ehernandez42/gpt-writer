import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

const mockPost = vi.fn()

vi.mock('../lib/api', () => ({
  APIError: class APIError extends Error {
    status: number

    constructor(status: number, message: string) {
      super(message)
      this.status = status
    }
  },
  api: {
    post: (...args: unknown[]) => mockPost(...args),
  },
}))

import { GeneratorForm } from './GeneratorForm'

describe('GeneratorForm', () => {
  it('shows a loading state and hides the previous result while generating', async () => {
    const user = userEvent.setup()
    let resolveRequest: ((value: { text: string; provider_used: string }) => void) | undefined

    mockPost
      .mockResolvedValueOnce({ text: 'Old result', provider_used: 'ollama' })
      .mockImplementationOnce(
        () =>
          new Promise<{ text: string; provider_used: string }>((resolve) => {
            resolveRequest = resolve
          }),
      )

    render(<GeneratorForm styles={[{ id: 'style-1', name: 'Style One' }]} />)

    await user.selectOptions(screen.getByRole('combobox'), 'style-1')
    await user.type(screen.getByRole('textbox'), 'First prompt')
    await user.click(screen.getByRole('button', { name: 'Generate' }))

    expect(await screen.findByText('Old result')).toBeInTheDocument()

    await user.clear(screen.getByRole('textbox'))
    await user.type(screen.getByRole('textbox'), 'Second prompt')
    await user.click(screen.getByRole('button', { name: 'Generate' }))

    expect(screen.getByRole('button', { name: 'Generating...' })).toBeDisabled()
    expect(screen.getByText('Generating response...')).toBeInTheDocument()
    expect(screen.queryByText('Old result')).not.toBeInTheDocument()

    resolveRequest?.({ text: 'New result', provider_used: 'ollama' })

    expect(await screen.findByText('New result')).toBeInTheDocument()
  })
})
