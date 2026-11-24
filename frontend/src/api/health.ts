export async function fetchHealth(): Promise<{ status: string; database: string }> {
  const response = await fetch('/api/health', { signal: AbortSignal.timeout(8000) })
  if (!response.ok) throw new Error('服务暂不可用，请稍后重试')
  return response.json()
}
