import { useEffect, useState, type ReactElement } from 'react'
import { api, errMsg, type ActiveSession, type TodayItem } from '../api'
import { clock, human } from '../format'

function elapsed(s: ActiveSession | null, now: number): number {
  if (!s) return 0
  let e = s.accumulated_seconds
  if (s.status === 'running' && s.last_resumed_at) {
    e += Math.max(0, Math.floor((now - new Date(s.last_resumed_at).getTime()) / 1000))
  }
  return e
}

interface Props {
  item: TodayItem
  onChange: () => void | Promise<void>
  onError: (msg: string) => void
}

export default function Stopwatch({ item, onChange, onError }: Props): ReactElement {
  const s = item.session
  const [now, setNow] = useState(() => Date.now())
  const [busy, setBusy] = useState(false)

  // Tick once a second, only while the stopwatch is actually running.
  const running = s?.status === 'running'
  useEffect(() => {
    if (!running) return
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [running])

  const act = async (fn: () => Promise<unknown>): Promise<void> => {
    setBusy(true)
    try {
      await fn()
      await onChange()
    } catch (e) {
      onError(errMsg(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="row stopwatch">
      <div className="grow">
        <div className="name">{item.name}</div>
        {item.duration_seconds ? (
          <div className="muted">Today: {human(item.duration_seconds)}</div>
        ) : null}
      </div>

      <div className={`clock ${s ? s.status : 'idle'}`}>{s ? clock(elapsed(s, now)) : '0:00'}</div>

      {!s && (
        <button
          className="btn primary"
          disabled={busy}
          onClick={() => act(() => api.startSession(item.metric_id))}
        >
          Start
        </button>
      )}
      {s?.status === 'running' && (
        <button className="btn" disabled={busy} onClick={() => act(() => api.pauseSession(s.id))}>
          Pause
        </button>
      )}
      {s?.status === 'paused' && (
        <button
          className="btn primary"
          disabled={busy}
          onClick={() => act(() => api.resumeSession(s.id))}
        >
          Resume
        </button>
      )}
      {s && (
        <button
          className="btn danger"
          disabled={busy}
          onClick={() => act(() => api.stopSession(s.id))}
        >
          Stop
        </button>
      )}
    </div>
  )
}
