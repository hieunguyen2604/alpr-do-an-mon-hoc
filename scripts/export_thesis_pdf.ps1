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

# Hai ban dung chung script nay:
#   docs/papers/            -> quyen do an tot nghiep
#   docs/papers/mon-hoc/    -> ban do an mon hoc
# CA HAI duong ra vi vay PHAI suy tu duong dan nguon, khong duoc dat cung.
# Loi nay da xay ra HAI lan, moi lan o mot duong ra khac nhau:
#   lan 1 -- ten trong nop/ dat cung "01-do-an-tot-nghiep.pdf", nen lan xuat
#            ban mon hoc dau tien chep de len ban tot nghiep trong nop/;
#   lan 2 -- sua xong lan 1 nhung $Dich van dat cung, nen ban mon hoc 43 trang
#            ghi de len docs/papers/thesis-full.pdf 86 trang cua ban tot nghiep.
# Bay gio ca hai deu suy tu $Nguon, va chi bi ghi de khi nguoi dung tu truyen.
param(
  [string]$Nguon = "D:\DATN\docs\papers\thesis-full.docx",
  [string]$Dich  = "",
  [string]$TenBanNop = ""
)

if (-not (Test-Path $Nguon)) {
  Write-Error "Khong thay $Nguon -- chay scripts/build_thesis.py truoc."
  exit 1
}

$Nguon = (Resolve-Path $Nguon).Path
if ([string]::IsNullOrWhiteSpace($Dich)) {
  $Dich = [IO.Path]::ChangeExtension($Nguon, '.pdf')
}

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

try {
  # KHONG mo ReadOnly. Truoc day mo ReadOnly nen so trang chi duoc tinh cho ban
  # PDF, con chinh tep .docx van giu gia tri cache: muc luc in ra cau nhac
  # "Mo tep trong Word roi bam Ctrl+A, F9", va cot Trang cua hai danh muc in ra
  # so 0. Ai mo .docx de doc — ke ca hoi dong — se thay dung ban chua cap nhat.
  $doc = $word.Documents.Open($Nguon)

  # Cap nhat muc luc: pandoc chen truong TOC nhung khong tinh so trang, nen neu
  # khong goi cai nay thi PDF ra mot muc luc rong. Goi HAI LAN: lan dau dien so
  # trang cho cac truong PAGEREF cua danh muc hinh/bang, lan hai tinh lai muc
  # luc sau khi do dai hai danh muc do da on dinh.
  foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
  $doc.Fields.Update() | Out-Null
  foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
  $doc.Fields.Update() | Out-Null

  # Ghi nguoc so trang da tinh vao chinh .docx, roi moi xuat PDF.
  $doc.Save()

  $doc.SaveAs([ref]$Dich, [ref]17)   # 17 = wdFormatPDF
  $so_trang = $doc.ComputeStatistics(2)   # 2 = wdStatisticPages
  $doc.Close([ref]$false)

  $mb = (Get-Item $Dich).Length / 1MB
  Write-Output ("[ok] PDF -> {0}  ({1:N1} MB, {2} trang)" -f $Dich, $mb, $so_trang)

  # Dong bo luon vao thu muc nop. build_thesis.py cung chep tep nay, nhung no
  # chi chay khi ai do dung lai quyen; neu chi xuat PDF thi ban nop se giu ban
  # PDF cu — dung cai loi ma thu muc nop sinh ra de tranh.
  #
  # Ten dich suy tu duong dan nguon, khong dat cung: hai ban deu chay script
  # nay va mot ten cung se lam ban nay de len ban kia.
  $ten = $TenBanNop
  if (-not $ten) {
    if ($Nguon -match 'mon-hoc') { $ten = "04-do-an-mon-hoc.pdf" }
    else                         { $ten = "01-do-an-tot-nghiep.pdf" }
  }
  $nop = Join-Path (Split-Path -Parent (Split-Path -Parent $PSCommandPath)) "nop"
  if (-not (Test-Path $nop)) { New-Item -ItemType Directory -Force $nop | Out-Null }
  Copy-Item $Dich (Join-Path $nop $ten) -Force
  Write-Output ("[ok] ban nop <- {0}" -f (Join-Path $nop $ten))

  # Chep luon .docx DA CAP NHAT TRUONG. build_thesis.py chep .docx vao nop/
  # TRUOC khi script nay chay, nen ban trong nop/ giu gia tri cache: muc luc in
  # cau nhac thao tac va cot Trang cua hai danh muc in so 0. Ai mo .docx trong
  # nop/ se doc dung ban chua cap nhat, du ban PDF canh no thi dung.
  $ten_docx = [System.IO.Path]::ChangeExtension($ten, "docx")
  Copy-Item $Nguon (Join-Path $nop $ten_docx) -Force
  Write-Output ("[ok] ban nop <- {0}" -f (Join-Path $nop $ten_docx))
}
finally {
  $word.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
