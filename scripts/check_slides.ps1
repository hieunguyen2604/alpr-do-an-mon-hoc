# Kiem tra bo slide da dung truoc khi in hoac trinh chieu.
#
# Hai loai loi, va loai thu hai la loai da lot luoi mot lan:
#
#   1. TRAN DAY  -- noi dung vuot qua canh duoi slide.
#   2. DE NHAU   -- hai khoi noi dung chong len nhau. PowerPoint KHONG cat chu
#                   khi no day hon o chua no; no cho chu tran ra va ve de len
#                   thu ben duoi. Mot cau dan hai dong trong o cao mot dong vi
#                   vay in de len bang ma phep do chieu cao KHONG phat hien.
#
# Chay:  powershell -File scripts/check_slides.ps1

param([string]$DeckPath = "D:\DATN\docs\slides\slides.pptx")

$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open($DeckPath, $true, $false, $false)
$H = $pres.PageSetup.SlideHeight
$loi = 0

foreach ($s in $pres.Slides) {
  # Chi xet cac khoi CO CHU va nam trong vung noi dung, bo qua khung trang tri.
  $khoi = @()
  foreach ($sh in $s.Shapes) {
    if ($sh.HasTextFrame -eq -1 -and $sh.TextFrame2.HasText -eq -1) {
      $khoi += [pscustomobject]@{
        Top    = $sh.Top
        Duoi   = $sh.Top + $sh.TextFrame2.TextRange.BoundHeight
        Chu    = ($sh.TextFrame2.TextRange.Text -split "`r")[0]
      }
    }
  }
  foreach ($t in $s.Shapes) {
    if ($t.HasTable -eq -1 -or $t.Type -eq 13) {
      $khoi += [pscustomobject]@{ Top = $t.Top; Duoi = $t.Top + $t.Height; Chu = "[bang/hinh]" }
    }
  }

  $khoi = $khoi | Sort-Object Top

  foreach ($k in $khoi) {
    if ($k.Duoi -gt $H) {
      $n = [Math]::Min(40, $k.Chu.Length)
      Write-Output ("  slide {0,2}  TRAN DAY {1,4} pt  <- {2}" -f $s.SlideIndex, [int]($k.Duoi - $H), $k.Chu.Substring(0, $n))
      $loi++
    }
  }
  for ($i = 0; $i -lt $khoi.Count - 1; $i++) {
    $a = $khoi[$i]; $b = $khoi[$i + 1]
    # Dung sai 6 pt: PowerPoint lam tron toa do khi do BoundHeight, nen mot
    # cho chong 2-3 pt la nhieu do chu khong phai loi nhin thay duoc.
    if ($a.Duoi -gt $b.Top + 6) {
      $n = [Math]::Min(34, $a.Chu.Length)
      $m = [Math]::Min(34, $b.Chu.Length)
      Write-Output ("  slide {0,2}  DE NHAU  {1,4} pt  <- '{2}' de len '{3}'" -f `
        $s.SlideIndex, [int]($a.Duoi - $b.Top), $a.Chu.Substring(0, $n), $b.Chu.Substring(0, $m))
      $loi++
    }
  }
}

Write-Output ("{0} slide | {1} loi" -f $pres.Slides.Count, $loi)
$pres.Close(); $ppt.Quit()
if ($loi -gt 0) { exit 1 }
