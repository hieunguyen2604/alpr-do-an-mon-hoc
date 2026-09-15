# Export defense-qa docx to PDF using Microsoft Word COM

$ErrorActionPreference = "Stop"

$docxPath = "D:\DATN\docs\slides\12-defense-qa-mon-hoc.docx"
$pdfPath = "D:\DATN\docs\slides\12-defense-qa-mon-hoc.pdf"

if (-not (Test-Path $docxPath)) {
    Write-Error "Khong tim thay $docxPath"
    exit 1
}

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
    Write-Host "Dang mo file: $docxPath..."
    $doc = $word.Documents.Open($docxPath)

    $doc.Fields.Update() | Out-Null
    $doc.Save()
    Write-Host "Dang xuat PDF: $pdfPath..."
    $doc.SaveAs([ref]$pdfPath, [ref]17) # 17 = wdFormatPDF

    $pages = $doc.ComputeStatistics(2)
    $doc.Close([ref]$false)
    Write-Host "[OK] Xuat thanh cong $pdfPath ($pages trang)"

    # Copy vao nop/
    $nopDir = "D:\DATN\nop"
    Copy-Item $docxPath (Join-Path $nopDir "05-bo-cau-hoi-phan-bien.docx") -Force
    Copy-Item $pdfPath (Join-Path $nopDir "05-bo-cau-hoi-phan-bien.pdf") -Force
    Write-Host "[OK] Da copy vao nop/05-bo-cau-hoi-phan-bien.docx va nop/05-bo-cau-hoi-phan-bien.pdf"
}
catch {
    Write-Error $_
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
