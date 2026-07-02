import { fireEvent, render, screen } from '@testing-library/react'

import { StyleForm } from '../components/StyleForm'


test('requires a name before submit', async () => {
  render(<StyleForm />)

  fireEvent.click(screen.getByRole('button', { name: /create style/i }))

  expect(await screen.findByText(/name is required/i)).toBeInTheDocument()
})
