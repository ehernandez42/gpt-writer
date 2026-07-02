import { FormEvent, useState } from 'react'

import { APIError, api } from '../lib/api'
import { ProviderBadge } from './ProviderBadge'

type Style = {
  id: string
  name: string
}

type GenerationRecord = {
  id?: string
  generation_id?: string
  style_id?: string
  prompt?: string
  generated_text?: string
  text?: string
  provider_used: string
  created_at?: string
  updated_at?: string
}

type GeneratorFormProps = {
  styles: Style[]
  onGenerated?: (generation: GenerationRecord) => void
}

export function GeneratorForm({ styles, onGenerated }: GeneratorFormProps) {
  const [styleId, setStyleId] = useState('')
  const [prompt, setPrompt] = useState('')
  const [result, setResult] = useState<GenerationRecord | null>(null)
  const [warning, setWarning] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setWarning('')
    setResult(null)
    setIsLoading(true)

    try {
      const response = await api.post<GenerationRecord>('/generate', { style_id: styleId, prompt })
      setResult(response)
      onGenerated?.({
        ...response,
        id: response.id ?? response.generation_id,
        style_id: response.style_id ?? styleId,
        prompt,
        generated_text: response.generated_text ?? response.text ?? '',
        updated_at: response.updated_at ?? response.created_at,
      })
    } catch (error) {
      if (error instanceof APIError && error.status === 503) {
        setWarning('All providers unavailable')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <select value={styleId} onChange={(event) => setStyleId(event.target.value)}>
          <option value="">Select a style</option>
          {styles.map((style) => (
            <option key={style.id} value={style.id}>
              {style.name}
            </option>
          ))}
        </select>
        <textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Generating...' : 'Generate'}
        </button>
      </form>
      {isLoading ? <p>Generating response...</p> : null}
      {warning ? <p>{warning}</p> : null}
      {result ? (
        <div>
          <ProviderBadge provider={result.provider_used} />
          <pre>{result.generated_text ?? result.text}</pre>
        </div>
      ) : null}
    </div>
  )
}
