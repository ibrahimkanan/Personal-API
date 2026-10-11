import { useState, type ReactElement } from 'react'
import { api, errMsg } from '../api'

interface Props {
  onClose: () => void
  onCreated: () => void | Promise<void>
}

type Kind = 'timer' | 'plain' | null

export default function AddItemDialog({ onClose, onCreated }: Props): ReactElement {
  const [kind, setKind] = useState<Kind>(null)
  const [valueType, setValueType] = useState<'boolean' | 'numeric'>('boolean')
  const [groupName, setGroupName] = useState('')
  const [unit, setUnit] = useState('')
  const [count, setCount] = useState(1)
  const [names, setNames] = useState<string[]>([''])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const changeCount = (n: number): void => {
    const c = Math.min(20, Math.max(1, n || 1))
    setCount(c)
    setNames((prev) => Array.from({ length: c }, (_, i) => prev[i] ?? ''))
  }

  const submit = async (): Promise<void> => {
    const cleaned = names.map((n) => n.trim())
    if (cleaned.some((n) => !n)) return setError('Give every item a name.')

    setBusy(true)
    setError(null)
    try {
      if (kind === 'timer') {
        await api.createMetric({ name: cleaned[0], type: 'duration' })
      } else if (valueType === 'numeric') {
        await api.createMetric({ name: cleaned[0], type: 'numeric', unit: unit.trim() || null })
      } else if (count === 1 && !groupName.trim()) {
        await api.createMetric({ name: cleaned[0], type: 'boolean' })
      } else {
        if (!groupName.trim()) {
          setBusy(false)
          return setError('Name the group (e.g. Prayers).')
        }
        await api.createGroup({ group_name: groupName.trim(), type: 'boolean', items: cleaned })
      }
      await onCreated()
      onClose()
    } catch (e) {
      setError(errMsg(e))
      setBusy(false)
    }
  }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Track something new</h3>

        {kind === null && (
          <div className="choices">
            <button className="choice" onClick={() => setKind('timer')}>
              <strong>With a timer</strong>
              <span className="muted">Gym, study… you start and stop a stopwatch</span>
            </button>
            <button className="choice" onClick={() => setKind('plain')}>
              <strong>Without a timer</strong>
              <span className="muted">Prayers, weight, calories… you just log it</span>
            </button>
          </div>
        )}

        {kind === 'timer' && (
          <label className="field">
            Name
            <input
              autoFocus
              value={names[0]}
              onChange={(e) => setNames([e.target.value])}
              placeholder="e.g. Gym"
            />
          </label>
        )}

        {kind === 'plain' && (
          <>
            <div className="seg">
              <button
                className={valueType === 'boolean' ? 'on' : ''}
                onClick={() => setValueType('boolean')}
              >
                Done / not done
              </button>
              <button
                className={valueType === 'numeric' ? 'on' : ''}
                onClick={() => {
                  setValueType('numeric')
                  changeCount(1)
                }}
              >
                A number
              </button>
            </div>

            {valueType === 'boolean' && (
              <>
                <label className="field">
                  Group name (optional for a single item)
                  <input
                    value={groupName}
                    onChange={(e) => setGroupName(e.target.value)}
                    placeholder="e.g. Prayers"
                  />
                </label>
                <label className="field">
                  How many items?
                  <input
                    type="number"
                    min={1}
                    max={20}
                    value={count}
                    onChange={(e) => changeCount(Number(e.target.value))}
                  />
                </label>
              </>
            )}

            {names.map((n, i) => (
              <label className="field" key={i}>
                {valueType === 'boolean' && count > 1 ? `Item ${i + 1}` : 'Name'}
                <input
                  value={n}
                  onChange={(e) =>
                    setNames((prev) => prev.map((p, j) => (j === i ? e.target.value : p)))
                  }
                  placeholder={valueType === 'numeric' ? 'e.g. Weight' : 'e.g. Fajr'}
                />
              </label>
            ))}

            {valueType === 'numeric' && (
              <label className="field">
                Unit (optional)
                <input
                  value={unit}
                  onChange={(e) => setUnit(e.target.value)}
                  placeholder="kg, kcal…"
                />
              </label>
            )}
          </>
        )}

        {error && <div className="error">{error}</div>}

        <div className="actions">
          <button className="btn" onClick={onClose}>
            Cancel
          </button>
          {kind && (
            <button className="btn primary" disabled={busy} onClick={submit}>
              Create
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
