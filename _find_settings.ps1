$paths = @(
    "$env:APPDATA\Cursor\User\settings.json",
    "$env:USERPROFILE\.cursor\settings.json",
    "$env:APPDATA\Cursor\User\globalStorage\cursor.cursor\settings.json"
)
foreach ($p in $paths) {
    if (Test-Path $p) {
        $item = Get-Item $p
        Write-Host "FOUND: $p  ($($item.Length) bytes, $($_.LastWriteTime))"
    } else {
        Write-Host "MISS:  $p"
    }
}
# Also list the Cursor User dir if it exists
$userDir = "$env:APPDATA\Cursor\User"
if (Test-Path $userDir) {
    Write-Host ""
    Write-Host "===== Files in $userDir ====="
    Get-ChildItem $userDir -Filter "*.json" | Select-Object Name, Length
}
