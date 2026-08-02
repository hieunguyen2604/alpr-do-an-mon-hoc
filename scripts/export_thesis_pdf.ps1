# Xuat thesis-full.docx sang PDF bang Microsoft Word.
#
# Vi sao khong dung pandoc: pandoc xuat PDF qua mot engine LaTeX (xelatex hoac
# pdflatex), va may nay khong co engine nao. Cai LaTeX chi de xuat mot tep PDF
# la doi mot phu thuoc vai GB lay mot viec ma Word da lam duoc.
#
# Vi sao khong dung Chromium nhu ban poster: poster la mot trang HTML viet tay
# nen dung duoc. Luan van thi da qua pandoc de co muc luc, danh so trang, kieu
# tieu de va bang -- dung lai DOCX giu nguyen toan bo dinh dang do.
#
# Chay:  powershell -File scripts/export_thesis_pdf.ps1

param(
  [string]$Nguon = "D:\DATN\docs\papers\thesis-full.docx",
  [string]$Dich  = "D:\DATN\docs\papers\thesis-full.pdf"
)

if (-not (Test-Path $Nguon)) {
  Write-Error "Khong thay $Nguon -- chay scripts/build_thesis.py truoc."
  exit 1
}

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
  $doc = $word.Documents.Open($Nguon, $false, $true)   # ReadOnly

  # Cap nhat muc luc: pandoc chen truong TOC nhung khong tinh so trang, nen neu
  # khong goi cai nay thi PDF ra mot muc luc rong.
  foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
  $doc.Fields.Update() | Out-Null

  $doc.SaveAs([ref]$Dich, [ref]17)   # 17 = wdFormatPDF
  $so_trang = $doc.ComputeStatistics(2)   # 2 = wdStatisticPages
  $doc.Close([ref]$false)

  $mb = (Get-Item $Dich).Length / 1MB
  Write-Output ("[ok] PDF -> {0}  ({1:N1} MB, {2} trang)" -f $Dich, $mb, $so_trang)
}
finally {
  $word.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
