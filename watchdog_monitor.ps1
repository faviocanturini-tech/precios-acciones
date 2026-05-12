# Watchdog para monitor_precios_intraday.py
# Verifica si el monitor está corriendo. Si no, lo inicia.
# Programar en Task Scheduler cada 10 minutos (lun-vie, 9:00-16:30 NY).

$BASE_DIR   = "C:\Users\favio\Desktop\TRADING"
$SCRIPT     = "monitor_precios_intraday.py"
$PYTHON     = "$BASE_DIR\.venv\Scripts\python.exe"
$LOG_FILE   = "$BASE_DIR\data\watchdog_monitor.log"

function Write-Log ($msg) {
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    "$ts  $msg" | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8
}

# Verificar horario de mercado (hora NY)
$nyZone   = [System.TimeZoneInfo]::FindSystemTimeZoneById("Eastern Standard Time")
$nyTime   = [System.TimeZoneInfo]::ConvertTime((Get-Date), $nyZone)
$nyHour   = $nyTime.Hour
$nyMinute = $nyTime.Minute
$nyDow    = $nyTime.DayOfWeek  # 0=Domingo, 6=Sabado

$esDiaSemana  = ($nyDow -ne [System.DayOfWeek]::Saturday) -and ($nyDow -ne [System.DayOfWeek]::Sunday)
$enHorario    = ($nyHour -gt 9) -or ($nyHour -eq 9 -and $nyMinute -ge 25)
$antesDelCierre = ($nyHour -lt 16) -or ($nyHour -eq 16 -and $nyMinute -le 35)

if (-not $esDiaSemana -or -not $enHorario -or -not $antesDelCierre) {
    Write-Log "Fuera de horario de mercado ($($nyTime.ToString('HH:mm')) NY, $nyDow). Sin accion."
    exit 0
}

# Verificar si el monitor ya está corriendo
$procesos = Get-WmiObject Win32_Process -Filter "name='python.exe'" |
            Where-Object { $_.CommandLine -like "*$SCRIPT*" }

if ($procesos) {
    $pid = ($procesos | Select-Object -First 1).ProcessId
    Write-Log "Monitor ya corriendo (PID $pid). OK."
    exit 0
}

# No está corriendo -> iniciarlo
Write-Log "Monitor NO encontrado. Iniciando..."

$cmdArgs = "/k title Monitor Intraday && cd /d $BASE_DIR && $PYTHON $SCRIPT"
Start-Process "cmd.exe" -ArgumentList $cmdArgs -WindowStyle Normal

Write-Log "Monitor iniciado."
