type ProviderBadgeProps = {
  provider: string
}

export function ProviderBadge({ provider }: ProviderBadgeProps) {
  return <span>{provider}</span>
}
