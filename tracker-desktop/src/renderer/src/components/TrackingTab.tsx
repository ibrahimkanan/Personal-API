import { useCallback, useEffect, useState, type ReactElement } from 'react'
import { api, errMsg, type TodayItem } from '../api'
import AddItemDialog from './AddItemDialog'
import Stopwatch from './Stopwatch'

interface Card {
  key: string
  title: string | null // group name, or null for a standalone item
  items: TodayItem[]
}

// Items sharing a group_name render as one card; everything else is its own.
function toCards(items: TodayItem[]): Card[] {
  const cards: Card[] = []
  const byGroup = new Map<string, Card>()
  for (const it of items) {
    if (it.group_name) {
      let c = byGroup.get(it.group_name)
      if (!c) {
        c = { key: `g:${it.group_name}`, title: it.group_name, items: [] }
        byGroup.set(it.group_name, c)
        cards.push(c)
      }
      c.items.push(it)
    } else {
      cards.push({ key: `m:${it.metric_id}`, title: null, items: [it] })
    }
  }
  return cards
}

function NumberRow({
  item,
  onChange,
  onError
}: {
  item: TodayItem
  onChange: () => void | Promise<void>
  onError: (m: string) => void
}): ReactElement {
  const [text, setText] = useState('')
  const save = async (): Promise<void> => {
    const v = Number(text)
    if (!text.trim() || Number.isNaN(v)) return
    try {
      await api.createLog({ metric_id: item.metric_id, value: v })
      setText('')
      await onChange()
    } catch (e) {
      onError(errMsg(e))
    }
  }
  return (
    <div className="row">
      <div className="grow">
        <div className="name">{item.name}</div>
        {item.value !== null && (
          <div className="muted">
            Latest today: {item.value}
            {item.unit ? ` ${item.unit}` : ''}
          </div>
        )}
      </div>
      <input
        className="num"
        type="number"
        step="any"
        value={text}
        placeholder={item.unit ?? 'value'}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && save()}
      />
      <button className="btn primary" onClick={save}>
        Log
      </button>
    </div>
  )
}

export default function TrackingTab(): ReactElement {
  const [items, setItems] = useState<TodayItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [adding, setAdding] = useState(false)

  const reload = useCallback(async (): Promise<void> => {
    try {
      setItems(await api.getToday())
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
    // Refresh when you come back to the window, so a day change (or an edit
    // from another device) shows up without restarting the app.
    const onFocus = (): void => void reload()
    window.addEventListener('focus', onFocus)
    return () => window.removeEventListener('focus', onFocus)
  }, [reload])

  const toggle = async (it: TodayItem): Promise<void> => {
    try {
      if (it.done && it.log_id !== null) await api.deleteLog(it.log_id)
      else await api.createLog({ metric_id: it.metric_id, value: 1 })
      await reload()
    } catch (e) {
      setError(errMsg(e))
    }
  }

  const cards = toCards(items)

  return (
    <div>
      <div className="toolbar">
        <button className="btn primary" onClick={() => setAdding(true)}>
          + Track something
        </button>
      </div>

      {error && (
        <div className="error">Can’t reach the API — is the backend running? ({error})</div>
      )}
      {loading && <div className="muted">Loading…</div>}
      {!loading && !error && cards.length === 0 && (
        <div className="empty">Nothing tracked yet. Add your first item.</div>
      )}

      {cards.map((card) => {
        const checks = card.items.filter((i) => i.type === 'boolean')
        const doneCount = checks.filter((i) => i.done).length
        return (
          <section className="card" key={card.key}>
            {card.title && (
              <header>
                <h2>{card.title}</h2>
                {checks.length > 0 && (
                  <span className="muted">
                    {doneCount}/{checks.length}
                  </span>
                )}
              </header>
            )}
            {card.title && checks.length > 0 && (
              <div className="bar">
                <div style={{ width: `${(doneCount / checks.length) * 100}%` }} />
              </div>
            )}

            {card.items.map((it) => {
              if (it.type === 'duration')
                return (
                  <Stopwatch key={it.metric_id} item={it} onChange={reload} onError={setError} />
                )
              if (it.type === 'numeric')
                return (
                  <NumberRow key={it.metric_id} item={it} onChange={reload} onError={setError} />
                )
              return (
                <label className={`row check ${it.done ? 'done' : ''}`} key={it.metric_id}>
                  <input type="checkbox" checked={it.done} onChange={() => toggle(it)} />
                  <span className="name grow">{it.name}</span>
                </label>
              )
            })}
          </section>
        )
      })}

      {adding && <AddItemDialog onClose={() => setAdding(false)} onCreated={reload} />}
    </div>
  )
}
