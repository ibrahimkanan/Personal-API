import { useState, type ReactElement } from 'react'
import TasksTab from './components/TasksTab'
import TrackingTab from './components/TrackingTab'

type Tab = 'tracking' | 'tasks'

export default function App(): ReactElement {
  const [tab, setTab] = useState<Tab>('tracking')
  const dateLabel = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric'
  })

  return (
    <div className="app">
      <header className="top">
        <h1>Personal Tracker</h1>
        <span className="muted">{dateLabel}</span>
      </header>

      <nav className="tabs">
        <button className={tab === 'tracking' ? 'on' : ''} onClick={() => setTab('tracking')}>
          Tracking
        </button>
        <button className={tab === 'tasks' ? 'on' : ''} onClick={() => setTab('tasks')}>
          Today’s tasks
        </button>
      </nav>

      <main>{tab === 'tracking' ? <TrackingTab /> : <TasksTab />}</main>
    </div>
  )
}
