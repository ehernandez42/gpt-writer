import { StyleCard } from './StyleCard'

type Style = {
  id: string
  name: string
}

type StyleListProps = {
  styles: Style[]
}

export function StyleList({ styles }: StyleListProps) {
  return (
    <ul>
      {styles.map((style) => (
        <StyleCard key={style.id} style={style} />
      ))}
    </ul>
  )
}
