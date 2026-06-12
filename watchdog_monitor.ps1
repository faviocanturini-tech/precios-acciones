# Watchdog para monitor_precios_intraday.py
# - Dentro de horario (9:25-4:10 NY): inicia el monitor si no está corriendo.
# - Después del cierre (>4:10 PM NY): detiene el monitor si está corriendo.
# Programar en Task Scheduler cada 10 minutos (lun-vie).

$BASE_DIR   = "C:\Users\favio\Desktop\TRADING"
$SCRIPT     = "monitor_precios_intraday.py"
$PYTHON     = "$BASE_DIR\.venv\Scripts\python.exe"
$LOG_FILE   = "$BASE_DIR\data\watchdog_monitor.log"

function Write-Log ($msg) {
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    "$ts  $msg" | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8
}

# Hora en NY
$nyZone   = [System.TimeZoneInfo]::FindSystemTimeZoneById("Eastern Standard Time")
$nyTime   = [System.TimeZoneInfo]::ConvertTime((Get-Date), $nyZone)
$nyHour   = $nyTime.Hour
$nyMinute = $nyTime.Minute
$nyDow    = $nyTime.DayOfWeek

$esDiaSemana    = ($nyDow -ne [System.DayOfWeek]::Saturday) -and ($nyDow -ne [System.DayOfWeek]::Sunday)
$enHorario      = ($nyHour -gt 9) -or ($nyHour -eq 9 -and $nyMinute -ge 25)
$antesDelCierre = ($nyHour -lt 16) -or ($nyHour -eq 16 -and $nyMinute -le 10)

# Buscar procesos monitor activos
$procesos = Get-WmiObject Win32_Process -Filter "name='python.exe'" |
            Where-Object { $_.CommandLine -like "*$SCRIPT*" }

if ($esDiaSemana -and $enHorario -and $antesDelCierre) {
    # Horario de mercado: iniciar si no está corriendo
    if ($procesos) {
        $pidActivo = ($procesos | Select-Object -First 1).ProcessId
        Write-Log "Monitor ya corriendo (PID $pidActivo). OK."
    } else {
        Write-Log "Monitor NO encontrado. Iniciando..."
        $cmdArgs = "/k title Monitor Intraday && cd /d $BASE_DIR && set PYTHONUNBUFFERED=1 && $PYTHON -u $SCRIPT"
        Start-Process "cmd.exe" -ArgumentList $cmdArgs -WindowStyle Normal
        Write-Log "Monitor iniciado."
    }
} elseif ($esDiaSemana -and $enHorario -and -not $antesDelCierre) {
    # Mercado cerrado (despues de 4:10 PM NY): detener si está corriendo
    if ($procesos) {
        foreach ($proc in $procesos) {
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
            Write-Log "Mercado cerrado (>4:10 PM NY). Monitor detenido (PID $($proc.ProcessId))."
        }
    } else {
        Write-Log "Mercado cerrado. Monitor no estaba corriendo. OK."
    }
} else {
    Write-Log "Fuera de horario ($($nyTime.ToString('HH:mm')) NY, $nyDow). Sin accion."
}
