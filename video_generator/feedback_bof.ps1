# feedback_bof.ps1
# Sistema simple de feedback para BOF Generator

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "  📝 SISTEMA DE FEEDBACK BOF" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Solicitar datos
$producto = Read-Host "`nProducto"
$puntuacion = Read-Host "Puntuación (1-5)"
$comentarios = Read-Host "Comentarios/Sugerencias"

# Validar puntuación
if ($puntuacion -notmatch '^[1-5]$') {
    Write-Host "`n❌ Puntuación inválida. Debe ser 1-5" -ForegroundColor Red
    exit 1
}

# Timestamp
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Crear entrada de feedback
$feedback = @"

==================================================
Fecha: $timestamp
Producto: $producto
Puntuación: $puntuacion/5
---
Comentarios:
$comentarios
==================================================

"@

# Guardar en archivo
$feedbackFile = "feedback_bof.txt"
Add-Content -Path $feedbackFile -Value $feedback -Encoding UTF8

# Confirmación
Write-Host "`n✅ Feedback guardado correctamente" -ForegroundColor Green
Write-Host "📄 Archivo: $feedbackFile" -ForegroundColor Gray

# Mostrar resumen
Write-Host "`n📊 RESUMEN:" -ForegroundColor Yellow
Write-Host "  Producto: $producto"
Write-Host "  Puntuación: $puntuacion/5"

# Emoji según puntuación
$emoji = switch ($puntuacion) {
    "1" { "😞" }
    "2" { "😕" }
    "3" { "😐" }
    "4" { "🙂" }
    "5" { "😃" }
}

Write-Host "`n$emoji Gracias por tu feedback!`n"
