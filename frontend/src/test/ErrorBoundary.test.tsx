import { render, screen } from '@testing-library/react'

import { ErrorBoundary } from '../components/ErrorBoundary'

function Boom() {
  throw new Error('boom')
}

test('renders fallback ui on render error', () => {
  render(
    <ErrorBoundary>
      <Boom />
    </ErrorBoundary>
  )

  expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
})
