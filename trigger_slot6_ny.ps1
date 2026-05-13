# Trigger Slot 6 - Solo ejecuta si es entre 8:00 y 9:10 AM hora LOCAL
$localTime = Get-Date
$hour = $localTime.Hour
$minute = $localTime.Minute

Write-Host "Hora local: $($localTime.ToString('HH:mm'))"

# Verificar si es entre 8:00 y 9:10 AM hora local
$enVentana = ($hour -eq 8) -or ($hour -eq 9 -and $minute -le 10)

if ($enVentana) {
    Write-Host "Ejecutando trigger Slot 6..."
    Set-Location "C:\Users\favio\Desktop\TRADING"

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
    $cmdArgs = '/k chcp 65001 >nul && title Slot 6 - Analisis Claude && echo. && echo ============================================ && echo  INICIANDO ANALISIS SLOT 6 - Por favor espere && echo  Claude esta cargando, esto puede tomar 30-60s && echo ============================================ && echo. && cd /d C:\Users\favio\Desktop\TRADING && claude -p "ejecuta el analisis Slot 6" --dangerously-skip-permissions & echo. & python verificar_slot6.py & echo. & echo Presione cualquier tecla para cerrar... & pause'
    Start-Process "cmd.exe" -ArgumentList $cmdArgs
}
else {
    Write-Host "No es hora de trigger (debe ser 8:00-9:10 AM local). Hora actual: $($localTime.ToString('HH:mm'))"
}
