import { render, screen } from '@testing-library/react'

import { ProviderBadge } from '../components/ProviderBadge'


test('renders provider label', () => {
  render(<ProviderBadge provider="ollama" />)

  expect(screen.getByText(/ollama/i)).toBeInTheDocument()
})
