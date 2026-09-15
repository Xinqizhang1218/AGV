param(
    [string]$TaskName = "AGVVisionDockerAutoStart"
)

$ErrorActionPreference = "Stop"

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Startup task removed: $TaskName"
} else {
    Write-Host "Task not found: $TaskName"
}
