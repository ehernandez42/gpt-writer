type StyleCardProps = {
  style: { id: string; name: string }
}

export function StyleCard({ style }: StyleCardProps) {
  return <li>{style.name}</li>
}
