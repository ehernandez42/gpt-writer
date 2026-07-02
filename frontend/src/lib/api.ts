const API_BASE = 'http://localhost:8000'

export class APIError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new APIError(response.status, await response.text())
  }
  return response.json() as Promise<T>
}

export const api = {
  async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`, init)
    return parseResponse<T>(response)
  },

  async get<T>(path: string): Promise<T> {
    return this.request<T>(path)
  },

  async post<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  },

  async patch<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  },

  async export(content: string, format: 'pdf' | 'docx', contentType: 'html'): Promise<Blob> {
    const url = `${API_BASE}/export`
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, format, content_type: contentType }),
    })

    if (!response.ok) throw new APIError(response.status, await response.text())
    return response.blob()
  },
}
