import { mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { randomUUID } from 'node:crypto'

const taskPattern = /(?:DILA_TASK=)?(DILA-TASK-\d{4,}|T\d{3,}|BUG-\d{3,})/i
const rolePattern = /DILA_AGENT=(claude-code|opencode|openrouter-qa)/i
const progressPattern = /DILA_PROGRESS=(\d{1,3})/i

function collectMetadata(value, acc = { text: '', visited: 0 }, depth = 0) {
  if (depth > 5 || acc.visited > 300 || value == null) return acc
  if (typeof value === 'string') {
    if (value.length < 4000) acc.text += `\n${value}`
    return acc
  }
  if (Array.isArray(value)) {
    for (const item of value.slice(0, 80)) collectMetadata(item, acc, depth + 1)
    return acc
  }
  if (typeof value === 'object') {
    for (const [key, item] of Object.entries(value).slice(0, 80)) {
      acc.visited += 1
      if (['prompt', 'text', 'content', 'message', 'lastAssistantMessage', 'last_assistant_message'].includes(key)) {
        collectMetadata(item, acc, depth + 1)
      } else if (depth < 3 && item && typeof item === 'object') {
        collectMetadata(item, acc, depth + 1)
      }
    }
  }
  return acc
}

function resolveEventDir() {
  const home = process.env.HERMES_HOME || path.join(process.env.LOCALAPPDATA || process.env.HOME || '.', 'hermes')
  return path.join(home, 'cache', 'agent-monitor', 'events')
}

export const AgentMonitor = async () => ({
  event: async ({ event }) => {
    try {
      const props = event?.properties || {}
      const info = props.info || props.session || {}
      const sessionId = props.sessionID || props.sessionId || info.sessionID || info.id || props.id
      if (!sessionId) return

      const type = String(event?.type || 'unknown')
      const metadata = collectMetadata(props).text
      const taskMatch = metadata.match(taskPattern)
      const roleMatch = metadata.match(rolePattern)
      const progressMatch = metadata.match(progressPattern)
      const progressValue = progressMatch ? Number(progressMatch[1]) : null
      const progress = Number.isInteger(progressValue) && progressValue >= 0 && progressValue <= 100 ? progressValue : null
      const isDone = /DILA_DONE=1/i.test(metadata)

      let status = 'working'
      if (type === 'session.created') status = 'queued'
      else if (type === 'session.idle') status = 'waiting'
      else if (type === 'session.error') status = 'error'
      else if (type === 'session.status') {
        const kind = props.status?.type || props.status || ''
        status = String(kind).toLowerCase().includes('idle') ? 'waiting' : 'working'
      }
      if (isDone) status = 'done'

      const localSession = String(sessionId).replace(/[^A-Za-z0-9_-]/g, '_').slice(0, 120)
      const directoryPath = resolveEventDir()
      await mkdir(directoryPath, { recursive: true })
      const record = {
        source: 'opencode-desktop',
        session_id: localSession,
        task_number: taskMatch ? taskMatch[1].toUpperCase() : null,
        agent_role: roleMatch ? roleMatch[1].toLowerCase() : 'opencode',
        event: type,
        status,
        progress: isDone ? 100 : progress,
        updated_at: new Date().toISOString()
      }
      const file = path.join(directoryPath, `${localSession}-${randomUUID()}.json`)
      await writeFile(file, JSON.stringify(record), { encoding: 'utf8', flag: 'wx' })
    } catch {
      // Monitoring must never interfere with the agent's work.
    }
  }
})
