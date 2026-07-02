import { useMutation } from '@tanstack/react-query'

import { api } from '../../lib/api'

export function useGenerate() {
  return useMutation({
    mutationFn: ({ styleId, prompt }: { styleId: string; prompt: string }) =>
      api.post('/generate', { style_id: styleId, prompt }),
  })
}
