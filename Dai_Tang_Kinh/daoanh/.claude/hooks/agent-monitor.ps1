$ErrorActionPreference = 'SilentlyContinue'
$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
try { $payload = $raw | ConvertFrom-Json -ErrorAction Stop } catch { exit 0 }

$session = [string]$payload.session_id
$event = [string]$payload.hook_event_name
if ([string]::IsNullOrWhiteSpace($session) -or [string]::IsNullOrWhiteSpace($event)) { exit 0 }

# Extract only task/progress markers in memory; never persist prompt or transcript text.
$metadataText = ([string]$payload.prompt) + "`n" + ([string]$payload.last_assistant_message)
$taskNumber = $null
$taskMatch = [regex]::Match($metadataText, '(?:DILA_TASK=)?(DILA-TASK-\d{4,}|T\d{3,}|BUG-\d{3,})')
if ($taskMatch.Success) { $taskNumber = $taskMatch.Groups[1].Value.ToUpperInvariant() }
$agentRole = 'claude-code'
$roleMatch = [regex]::Match($metadataText, 'DILA_AGENT=(claude-code|opencode|openrouter-qa)', 'IgnoreCase')
if ($roleMatch.Success) { $agentRole = $roleMatch.Groups[1].Value.ToLowerInvariant() }
$progress = $null
$progressMatch = [regex]::Match($metadataText, 'DILA_PROGRESS=(\d{1,3})')
if ($progressMatch.Success) {
  $candidate = [int]$progressMatch.Groups[1].Value
  if ($candidate -ge 0 -and $candidate -le 100) { $progress = $candidate }
}

$status = switch ($event) {
  'SessionStart' { 'queued' }
  'UserPromptSubmit' { 'working' }
  'PreToolUse' { 'working' }
  'PostToolUse' { 'working' }
  'StopFailure' { 'error' }
  'SessionEnd' { 'stopped' }
  'Stop' { if ($metadataText -match 'DILA_DONE=1') { 'done' } else { 'waiting' } }
  default { 'working' }
}
if ($status -eq 'done') { $progress = 100 }

$localData = [Environment]::GetEnvironmentVariable('LOCALAPPDATA')
if ([string]::IsNullOrWhiteSpace($localData)) { exit 0 }
$hermesHome = [Environment]::GetEnvironmentVariable('HERMES_HOME')
if ([string]::IsNullOrWhiteSpace($hermesHome)) { $hermesHome = Join-Path $localData 'hermes' }
$eventsDir = Join-Path $hermesHome 'cache\agent-monitor\events'
New-Item -ItemType Directory -Path $eventsDir -Force | Out-Null
$safeSession = [regex]::Replace($session, '[^A-Za-z0-9_-]', '_')
$record = [ordered]@{
  source = 'claude-code-desktop'
  session_id = $safeSession
  task_number = $taskNumber
  agent_role = $agentRole
  event = $event
  status = $status
  progress = $progress
  updated_at = [DateTime]::UtcNow.ToString('o')
}
$file = Join-Path $eventsDir ($safeSession + '-' + [guid]::NewGuid().ToString('N') + '.json')
$json = $record | ConvertTo-Json -Compress
[System.IO.File]::WriteAllText($file, $json, (New-Object System.Text.UTF8Encoding($false)))
