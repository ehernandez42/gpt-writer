import { render, screen } from '@testing-library/react'

import { GenerationEditor } from '../components/GenerationEditor'


test('renders export buttons', () => {
  render(<GenerationEditor generatedText="hello" />)

  expect(screen.getByRole('button', { name: /export pdf/i })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /export docx/i })).toBeInTheDocument()
})
