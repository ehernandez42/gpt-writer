import { FormEvent, useState } from 'react'

import { api } from '../lib/api'
import { queryClient } from '../lib/queryClient'
import { FileUploader } from './FileUploader'

export function StyleForm() {
  const [name, setName] = useState('')
  const [files, setFiles] = useState<FileList | null>(null)
  const [error, setError] = useState('')

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()

    if (!name.trim()) {
      setError('Name is required')
      return
    }

    if (!files || files.length === 0) {
      setError('Files are required')
      return
    }

    setError('')
    const formData = new FormData()
    formData.append('name', name)
    Array.from(files).forEach((file) => formData.append('files', file))
    await api.request('/styles', { method: 'POST', body: formData })
    await queryClient.invalidateQueries({ queryKey: ['styles'] })
    setName('')
    setFiles(null)
  }

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Name
        <input name="name" value={name} onChange={(event) => setName(event.target.value)} />
      </label>
      <FileUploader onChange={setFiles} />
      {error ? <p>{error}</p> : null}
      <button type="submit">Create Style</button>
    </form>
  )
}
