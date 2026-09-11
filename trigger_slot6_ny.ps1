# Trigger Slot 6 - Solo ejecuta si es entre 8:00 y 9:10 AM hora LOCAL
$localTime = Get-Date
$hour = $localTime.Hour
$minute = $localTime.Minute

Write-Host "Hora local: $($localTime.ToString('HH:mm'))"

# Verificar si es entre 8:00 y 9:10 AM hora local
$enVentana = ($hour -eq 8) -or ($hour -eq 9 -and $minute -le 10)

if ($enVentana) {
    Set-Location "C:\Users\favio\Desktop\TRADING"

    # Verificar si ya existe análisis del día antes de hacer nada
    $hoy = $localTime.ToString('yyyy-MM-dd')
    $decisionesFile = "data\decisiones_claude.json"
    $yaExiste = $false

    if (Test-Path $decisionesFile) {
        try {
            $content = Get-Content $decisionesFile -Raw -Encoding UTF8
            $obj = $content | ConvertFrom-Json
            foreach ($d in $obj.decisiones) {
                $fa = $d.fecha_analisis
                $ft = $d.fecha_trading
                if (($fa -and $fa.ToString().StartsWith($hoy)) -or ($ft -and $ft.ToString().StartsWith($hoy))) {
                    $yaExiste = $true
                    break
                }
            }
        } catch {}
    }

    if ($yaExiste) {
        Write-Host "Analisis Slot 6 ya existe para $hoy - no se ejecuta de nuevo."
        Write-Host "(La ventana se cerrara en 5 segundos...)"
        Start-Sleep -Seconds 5
        exit 0
    }

    Write-Host "Ejecutando trigger Slot 6..."

    # Crear archivo de trigger
    $trigger = @{
        fecha = $localTime.ToString('yyyy-MM-dd')
        hora_generacion = $localTime.ToString('HH:mm:ss')
        estado = "pendiente"
        plataforma = "IBKR-UK"
        modo = "Real"
        mensaje = "Datos listos para análisis de Claude - Slot 6"
    } | ConvertTo-Json

    $trigger | Out-File -FilePath "data\trigger_analisis_claude.json" -Encoding UTF8

    # Git commit y push con LOCK compartido (mismo lock que git_utils.py, para no
    # chocar con la GUI ni los syncs) + pull --rebase antes del push + REINTENTO.
    $repoDir = "C:\Users\favio\Desktop\TRADING"
    $lockFile = Join-Path $repoDir ".git\trading_git_lock"
    $lockAcquired = $false
    $deadline = (Get-Date).AddSeconds(90)
    while ((Get-Date) -lt $deadline) {
        try {
            $fs = [System.IO.File]::Open($lockFile, [System.IO.FileMode]::CreateNew)
            $b = [System.Text.Encoding]::ASCII.GetBytes("$PID ps1")
            $fs.Write($b, 0, $b.Length); $fs.Close()
            $lockAcquired = $true; break
        } catch {
            if (Test-Path $lockFile) {
                $age = ((Get-Date) - (Get-Item $lockFile).LastWriteTime).TotalSeconds
                if ($age -gt 180) { Remove-Item $lockFile -Force -ErrorAction SilentlyContinue; continue }
            }
            Start-Sleep -Milliseconds 500
        }
    }
    try {
        # Limpiar rebase/merge colgado antes de operar
        if ((Test-Path "$repoDir\.git\rebase-merge") -or (Test-Path "$repoDir\.git\rebase-apply")) {
            git rebase --abort 2>$null
            Remove-Item "$repoDir\.git\rebase-merge","$repoDir\.git\rebase-apply" -Recurse -Force -ErrorAction SilentlyContinue
        }
        if (Test-Path "$repoDir\.git\MERGE_HEAD") { git merge --abort 2>$null }

        git add data\trigger_analisis_claude.json
        git commit -m "Trigger Slot 6 - $($localTime.ToString('yyyy-MM-dd'))"
        $pushed = $false
        for ($i = 1; $i -le 3; $i++) {
            git pull --rebase --autostash origin main | Out-Null
            git push origin main
            if ($LASTEXITCODE -eq 0) { $pushed = $true; break }
            Start-Sleep -Seconds 1
        }
        if ($pushed) { Write-Host "Trigger creado y enviado a GitHub" }
        else { Write-Host "[WARN] Trigger commiteado local; el push no entro (se reconciliara en el proximo sync)" }
    } finally {
        if ($lockAcquired) { Remove-Item $lockFile -Force -ErrorAction SilentlyContinue }
    }

    # Abrir Claude Code con prompt inicial para activar el análisis
    Write-Host "Abriendo Claude Code con análisis automático..."
    $PYTHON  = "C:\Users\favio\Desktop\TRADING\.venv\Scripts\python.exe"
    $cmdArgs = "/k chcp 65001 >nul && title Slot 6 - Analisis Claude && cd /d C:\Users\favio\Desktop\TRADING && $PYTHON run_slot6_cmd.py"
    Start-Process "cmd.exe" -ArgumentList $cmdArgs
}
else {
    Write-Host "No es hora de trigger (debe ser 8:00-9:10 AM local). Hora actual: $($localTime.ToString('HH:mm'))"
}

# Pausa para poder leer los mensajes antes de que la ventana se cierre.
# Subir el numero si se quiere mas tiempo (o cambiar por 'Read-Host' para que no cierre sola).
Write-Host ""
Write-Host "(La ventana se cerrara en 5 segundos...)"
Start-Sleep -Seconds 5
