param(
    [string]$DeckPath = "D:\DATN\docs\slides\12-slides-mon-hoc.pptx"
)

$fullPath = (Resolve-Path $DeckPath).Path
$pdfPath = [System.IO.Path]::ChangeExtension($fullPath, ".pdf")

$ppt = New-Object -ComObject PowerPoint.Application
try {
    $pres = $ppt.Presentations.Open($fullPath, $false, $false, $false)
    $pres.SaveAs($pdfPath, 32)
    $pres.Close()
    Write-Output "[ok] Exported PDF: $pdfPath"
}
finally {
    $ppt.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) | Out-Null
}
