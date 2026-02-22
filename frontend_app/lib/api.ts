export function getApiBaseUrl(): string {
  // Local dev: Next runs on :3000, backend on :8000.
  // Be robust to using 127.0.0.1, machine hostname, etc.
  if (typeof window !== 'undefined') {
    const { hostname, port, protocol } = window.location
    if (port === '3000') {
      const isHttps = protocol === 'https:'
      const backendProtocol = isHttps ? 'https:' : 'http:'
      // On macOS, localhost may resolve to IPv6 (::1) while uvicorn is bound to 127.0.0.1.
      // Force IPv4 loopback for local dev to avoid silent API connection failures.
      const backendHost = hostname === 'localhost' ? '127.0.0.1' : hostname
      return `${backendProtocol}//${backendHost}:8000`
    }
  }

  // Databricks Apps / static export served by backend: same origin
  return ''
}

export async function apiFetch(path: string, init?: RequestInit) {
  const base = getApiBaseUrl()
  const url = path.startsWith('http') ? path : `${base}${path}`
  return fetch(url, init)
}

