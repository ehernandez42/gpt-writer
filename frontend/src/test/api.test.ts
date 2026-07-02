import { APIError } from '../lib/api'


test('api error preserves status code', () => {
  const error = new APIError(503, 'All providers unavailable')

  expect(error.status).toBe(503)
  expect(error.message).toBe('All providers unavailable')
})
