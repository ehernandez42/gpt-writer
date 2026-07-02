import { QueryClientProvider } from '@tanstack/react-query'
import { Navigate, Route, Routes } from 'react-router-dom'

import { Layout } from './components/Layout'
import { queryClient } from './lib/queryClient'
import { GeneratePage } from './routes/GeneratePage'
import { StylesPage } from './routes/StylesPage'

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/styles" replace />} />
          <Route path="/styles" element={<StylesPage />} />
          <Route path="/generate" element={<GeneratePage />} />
        </Route>
      </Routes>
    </QueryClientProvider>
  )
}
