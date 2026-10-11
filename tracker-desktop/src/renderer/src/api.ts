// All communication with the FastAPI backend lives here.
const BASE: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export type MetricType = 'numeric' | 'boolean' | 'duration'

export interface ActiveSession {
  id: number
  status: 'running' | 'paused'
  accumulated_seconds: number
  last_resumed_at: string | null
}

export interface TodayItem {
  metric_id: number
  name: string
  type: MetricType
  unit: string | null
  group_name: string | null
  done: boolean
  log_id: number | null
  value: number | null
  duration_seconds: number | null
  session: ActiveSession | null
}

export type TaskStatus = 'pending' | 'done' | 'late'

export interface Task {
  id: number
  title: string
  points: number
  status: TaskStatus
  due_date: string | null
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...init
  })
  if (!res.ok) {
    throw new Error(`${res.status}: ${await res.text()}`)
  }
  return (await res.json()) as T
}

const post = <T>(path: string, body?: unknown): Promise<T> =>
  req<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })

export const api = {
  getToday: () => req<TodayItem[]>('/metrics/today'),
  createMetric: (m: { name: string; type: MetricType; unit?: string | null }) =>
    post('/metrics', m),
  createGroup: (g: { group_name: string; type: MetricType; items: string[] }) =>
    post('/metrics/group', g),

  createLog: (l: { metric_id: number; value?: number }) => post('/logs', l),
  deleteLog: (id: number) => req<{ ok: boolean }>(`/logs/${id}`, { method: 'DELETE' }),

  startSession: (metric_id: number) => post('/sessions/start', { metric_id }),
  pauseSession: (id: number) => post(`/sessions/${id}/pause`),
  resumeSession: (id: number) => post(`/sessions/${id}/resume`),
  stopSession: (id: number) => post(`/sessions/${id}/stop`),

  getTasksToday: () => req<Task[]>('/tasks/today'),
  createTask: (t: { title: string; points: number }) => post<Task>('/tasks', t),
  updateTask: (id: number, patch: { status?: TaskStatus; title?: string; points?: number }) =>
    req<Task>(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(patch) }),
  deleteTask: (id: number) => req<{ ok: boolean }>(`/tasks/${id}`, { method: 'DELETE' })
}

export const errMsg = (e: unknown): string => (e instanceof Error ? e.message : String(e))
