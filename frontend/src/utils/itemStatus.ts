const LABELS: Record<string, string> = {
  pending: '招领中',
  matched: '匹配中',
  claimed: '已认领',
  expired: '已过期',
  offline: '已下架',
}

export function itemStatusLabel(status: string | undefined | null): string {
  if (!status) return '—'
  return LABELS[status] ?? status
}
