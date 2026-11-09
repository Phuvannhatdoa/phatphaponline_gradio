# Block git write commands (add/commit/reset/push --force)
# PreToolUse hook that intercepts and blocks git write operations

param (
    [string]$command,
    [string]$args,
    [string]$filePath
)

# Block all git write commands
if ($command -match '^git\s+(add|commit|reset|push)' -and $args -notmatch '--force' -and $args -notmatch '--dry-run' -notmatch '--no-commit' -notmatch '--no-verify' -notmatch '--quiet' -notmatch '--no-ff' -notmatch '--no-edit' -notmatch '--no-ff' -notmatch '--no-edit' -notmatch '--no-ff' -notmatch '--no-edit' ) {
    Write-Error "Git write command blocked: $command $args on $filePath"
    exit 1
}

# Allow dry-run, no-commit, etc. for testing
if ($args -match '--dry-run' -or $args -match '--no-commit' -or $args -match '--no-verify' -or $args -match '--quiet') {
    Write-Verbose "Git command allowed (exempt): $command $args"
    exit 0
}

exit 1
