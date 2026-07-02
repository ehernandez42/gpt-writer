import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import App from '../App'


test('renders app navigation', () => {
  render(
    <MemoryRouter>
      <App />
    </MemoryRouter>
  )

  expect(screen.getByText(/styles/i)).toBeInTheDocument()
  expect(screen.getByText(/generate/i)).toBeInTheDocument()
})
