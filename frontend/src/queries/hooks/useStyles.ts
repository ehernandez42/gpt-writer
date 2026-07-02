import { useMutation, useQuery } from '@tanstack/react-query'

import { api } from '../../lib/api'

export function useStyles() {
  return useQuery({ queryKey: ['styles'], queryFn: () => api.get('/styles') })
}

export function useStyle(id: string) {
  return useQuery({ queryKey: ['styles', id], queryFn: () => api.get(`/styles/${id}`) })
}

export function useCreateStyle() {
  return useMutation({ mutationFn: (data: FormData) => api.request('/styles', { method: 'POST', body: data }) })
}
