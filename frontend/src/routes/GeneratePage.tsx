import { useEffect, useMemo, useState } from 'react'

import { GenerationEditor } from '../components/GenerationEditor'
import { GeneratorForm } from '../components/GeneratorForm'
import { api } from '../lib/api'
import { useStyles } from '../queries/hooks/useStyles'

type GenerationRecord = {
  id: string
  style_id: string
  prompt: string
  generated_text: string
  provider_used: string
  created_at: string
  updated_at?: string
}

export function GeneratePage() {
  const { data, error } = useStyles()
  const [generations, setGenerations] = useState<GenerationRecord[]>([])
  const [selectedGenerationId, setSelectedGenerationId] = useState<string | null>(null)
  const [editorText, setEditorText] = useState('')
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')

  useEffect(() => {
    let isMounted = true

    async function loadGenerations() {
      const response = await api.get<GenerationRecord[]>('/generations')
      if (isMounted) {
        setGenerations(response)
      }
    }

    void loadGenerations()

    return () => {
      isMounted = false
    }
  }, [])

  const selectedGeneration = useMemo(
    () => generations.find((generation) => generation.id === selectedGenerationId) ?? null,
    [generations, selectedGenerationId],
  )

  useEffect(() => {
    if (!selectedGenerationId || !selectedGeneration) {
      return
    }
    if (editorText === selectedGeneration.generated_text) {
      return
    }

    setSaveStatus('saving')
    const timeout = window.setTimeout(async () => {
      try {
        const updated = await api.patch<GenerationRecord>(`/generations/${selectedGenerationId}`, {
          generated_text: editorText,
        })
        setGenerations((current) =>
          current.map((generation) =>
            generation.id === updated.id ? updated : generation,
          ),
        )
        setSaveStatus('saved')
      } catch {
        setSaveStatus('error')
      }
    }, 800)

    return () => {
      window.clearTimeout(timeout)
    }
  }, [editorText, selectedGeneration, selectedGenerationId])

  function handleGenerated(generation: Partial<GenerationRecord> & { id?: string; generation_id?: string; generated_text?: string }) {
    const normalized: GenerationRecord = {
      id: generation.id ?? generation.generation_id ?? crypto.randomUUID(),
      style_id: generation.style_id ?? '',
      prompt: generation.prompt ?? '',
      generated_text: generation.generated_text ?? '',
      provider_used: generation.provider_used ?? 'unknown',
      created_at: generation.created_at ?? new Date().toISOString(),
      updated_at: generation.updated_at ?? generation.created_at ?? new Date().toISOString(),
    }

    setGenerations((current) => [normalized, ...current.filter((item) => item.id !== normalized.id)])
    setSelectedGenerationId(normalized.id)
    setEditorText(normalized.generated_text)
    setSaveStatus('saved')
  }

  function handleSelectGeneration(generation: GenerationRecord) {
    setSelectedGenerationId(generation.id)
    setEditorText(generation.generated_text)
    setSaveStatus('saved')
  }

  return (
    <div>
      <h1>Generate</h1>
      {error ? <p>Failed to load styles</p> : null}
      <GeneratorForm
        styles={(data as Array<{ id: string; name: string }>) ?? []}
        onGenerated={handleGenerated}
      />
      <section>
        <h2>Past Generations</h2>
        <ul>
          {generations.map((generation) => (
            <li key={generation.id}>
              <button type="button" onClick={() => handleSelectGeneration(generation)}>
                {generation.prompt || generation.id}
              </button>
            </li>
          ))}
        </ul>
      </section>
      {selectedGenerationId ? (
        <GenerationEditor content={editorText} onChange={setEditorText} saveStatus={saveStatus} />
      ) : null}
    </div>
  )
}
