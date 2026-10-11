import { useCallback, useEffect, useState, type ReactElement } from 'react'
import { api, errMsg, type Task } from '../api'

const ORDER = { late: 0, pending: 1, done: 2 } as const

// YYYY-MM-DD in the local timezone
const localISO = (): string => new Date().toLocaleDateString('en-CA')

export default function TasksTab(): ReactElement {
  const [tasks, setTasks] = useState<Task[]>([])
  const [title, setTitle] = useState('')
  const [points, setPoints] = useState(1)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const reload = useCallback(async (): Promise<void> => {
    try {
      setTasks(await api.getTasksToday())
      setError(null)
    } catch (e) {
      setError(errMsg(e))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial data fetch on mount
    void reload()
    const onFocus = (): void => void reload()
    window.addEventListener('focus', onFocus)
    return () => window.removeEventListener('focus', onFocus)
  }, [reload])

  const run = async (fn: () => Promise<unknown>): Promise<void> => {
    try {
      await fn()
      await reload()
    } catch (e) {
      setError(errMsg(e))
    }
  }

  const add = async (): Promise<void> => {
    const t = title.trim()
    if (!t) return
    await run(() => api.createTask({ title: t, points }))
    setTitle('')
  }

  const toggle = (t: Task): Promise<void> => {
    // Un-checking an old task puts it back to 'late', not 'pending',
    // so it doesn't vanish from the list until the nightly rollover.
    const undone = t.due_date && t.due_date < localISO() ? 'late' : 'pending'
    return run(() => api.updateTask(t.id, { status: t.status === 'done' ? undone : 'done' }))
  }

  const sorted = [...tasks].sort((a, b) => ORDER[a.status] - ORDER[b.status] || a.id - b.id)
  const earned = tasks.filter((t) => t.status === 'done').reduce((sum, t) => sum + t.points, 0)
  const possible = tasks.reduce((sum, t) => sum + t.points, 0)

  return (
    <div>
      <div className="toolbar add-task">
        <input
          className="grow"
          value={title}
          placeholder="New task for today…"
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && add()}
        />
        <input
          className="num"
          type="number"
          min={0}
          value={points}
          title="Points"
          onChange={(e) => setPoints(Math.max(0, Number(e.target.value) || 0))}
        />
        <button className="btn primary" onClick={add}>
          Add
        </button>
      </div>

      {error && (
        <div className="error">Can’t reach the API — is the backend running? ({error})</div>
      )}
      {loading && <div className="muted">Loading…</div>}
      {!loading && !error && tasks.length === 0 && <div className="empty">No tasks for today.</div>}

      {tasks.length > 0 && (
        <div className="muted points">
          Points: {earned} / {possible}
        </div>
      )}

      <section className="card">
        {sorted.map((t) => (
          <div className={`row check ${t.status === 'done' ? 'done' : ''}`} key={t.id}>
            <input type="checkbox" checked={t.status === 'done'} onChange={() => toggle(t)} />
            <span className="name grow">{t.title}</span>
            {t.status === 'late' && <span className="badge late">late</span>}
            <span className="badge">{t.points} pt</span>
            <button className="icon" title="Delete" onClick={() => run(() => api.deleteTask(t.id))}>
              ✕
            </button>
          </div>
        ))}
      </section>
    </div>
  )
}
