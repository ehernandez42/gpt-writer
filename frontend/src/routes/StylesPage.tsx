import { StyleForm } from '../components/StyleForm'
import { StyleList } from '../components/StyleList'
import { useStyles } from '../queries/hooks/useStyles'

export function StylesPage() {
  const { data, error } = useStyles()

  return (
    <div>
      <h1>Style Studio</h1>
      <StyleForm />
      {error ? <p>Failed to load styles</p> : null}
      <StyleList styles={(data as Array<{ id: string; name: string }>) ?? []} />
    </div>
  )
}
