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

    # Git commit y push
    git add data\trigger_analisis_claude.json
    git commit -m "Trigger Slot 6 - $($localTime.ToString('yyyy-MM-dd'))"
    git push origin main

    Write-Host "Trigger creado y enviado a GitHub"

    # Abrir Claude Code con prompt inicial para activar el análisis
    Write-Host "Abriendo Claude Code con análisis automático..."
    $PYTHON  = "C:\Users\favio\Desktop\TRADING\.venv\Scripts\python.exe"
    $cmdArgs = "/k chcp 65001 >nul && title Slot 6 - Analisis Claude && cd /d C:\Users\favio\Desktop\TRADING && $PYTHON run_slot6_cmd.py"
    Start-Process "cmd.exe" -ArgumentList $cmdArgs
}
else {
    Write-Host "No es hora de trigger (debe ser 8:00-9:10 AM local). Hora actual: $($localTime.ToString('HH:mm'))"
}
