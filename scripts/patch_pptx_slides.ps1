param([string]$DeckPath = "D:\DATN\docs\slides\12-slides-mon-hoc.pptx")

if (-not (Test-Path $DeckPath)) {
    Write-Output "Deck not found: $DeckPath"
    exit 0
}

$fullPath = (Resolve-Path $DeckPath).Path
$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open($fullPath, $false, $false, $false)

# 1. Slide 8: Adjust Title Font Size to 28 pt so it fits on 1 line and does not overlap subtitle
if (8 -le $pres.Slides.Count) {
    $s8 = $pres.Slides.Item(8)
    foreach ($sh in $s8.Shapes) {
        if ($sh.HasTextFrame -eq -1 -and $sh.Top -lt 50) {
            $sh.TextFrame.TextRange.Font.Size = 28
        }
    }
}

# 2. Slide 2: Preserve numbered list (1, 2, 3, 4)
if (2 -le $pres.Slides.Count) {
    $s2 = $pres.Slides.Item(2)
    foreach ($sh in $s2.Shapes) {
        if ($sh.HasTextFrame -eq -1 -and $sh.Top -gt 50 -and $sh.Top -lt 200) {
            $tf = $sh.TextFrame
            for ($p = 1; $p -le $tf.TextRange.Paragraphs().Count; $p++) {
                $para = $tf.TextRange.Paragraphs($p)
                $para.ParagraphFormat.Bullet.Type = 2 # ppBulletNumbered
                $para.ParagraphFormat.Bullet.Visible = -1
            }
        }
    }
}

# 3. Disable bullets on subtitle/lead sentences for all non-bullet slides
foreach ($slide in $pres.Slides) {
    if ($slide.SlideIndex -notin @(3, 19, 22)) {
        if ($slide.SlideIndex -notin @(1, 23)) {
            foreach ($sh in $slide.Shapes) {
                if ($sh.HasTextFrame -eq -1 -and $sh.Top -gt 50 -and $sh.Top -lt 200) {
                    $tf = $sh.TextFrame
                    if ($tf.HasText -eq -1) {
                        for ($p = 1; $p -le $tf.TextRange.Paragraphs().Count; $p++) {
                            $tf.TextRange.Paragraphs($p).ParagraphFormat.Bullet.Type = 0 # ppBulletNone
                        }
                    }
                }
            }
        }
    }
}

# 4. Slide 3: Apply literal hyphen "- " prefix, remove bullet glyphs completely (immune to font/reader '0' bug)
if (3 -le $pres.Slides.Count) {
    $s3 = $pres.Slides.Item(3)
    foreach ($sh in $s3.Shapes) {
        if ($sh.HasTextFrame -eq -1 -and $sh.Top -gt 50 -and $sh.Top -lt 300) {
            $tf = $sh.TextFrame
            if ($tf.HasText -eq -1) {
                # Delete empty or stray '0' or lone '-' paragraphs
                for ($p = $tf.TextRange.Paragraphs().Count; $p -ge 1; $p--) {
                    $para = $tf.TextRange.Paragraphs($p)
                    $trimmed = $para.Text.Trim()
                    if ($trimmed -eq "" -or $trimmed -eq "0" -or $trimmed -eq "-" -or $trimmed -eq [string][char]8211 -or $trimmed -eq [string][char]8212) {
                        if ($tf.TextRange.Paragraphs().Count -gt 1) {
                            $para.Delete()
                        }
                    }
                }
                
                # Format each of the 4 paragraphs with literal "- " and Bullet.Type = 0
                for ($p = 1; $p -le $tf.TextRange.Paragraphs().Count; $p++) {
                    $para = $tf.TextRange.Paragraphs($p)
                    $para.ParagraphFormat.Bullet.Type = 0
                    $para.ParagraphFormat.Bullet.Visible = 0
                    
                    # Strip any manual leading dash, bullet, or '0' prefix while keeping remaining bold runs
                    if ($para.Text.StartsWith("- ") -or $para.Text.StartsWith("0 ") -or $para.Text.StartsWith("0`t") -or $para.Text.StartsWith([string][char]8226 + " ")) {
                        $para.Characters(1, 2).Delete()
                    } elseif ($para.Text.StartsWith([string][char]8226) -or $para.Text.StartsWith("0") -or $para.Text.StartsWith("-")) {
                        $para.Characters(1, 1).Delete()
                    }
                    
                    if (-not $para.Text.StartsWith("- ")) {
                        $ins = $para.InsertBefore("- ")
                        $ins.Font.Name = "Arial"
                        $ins.Font.Bold = 0
                    }
                    
                    $para.Font.Name = "Arial"
                    $para.Font.Size = 15
                    $para.ParagraphFormat.SpaceBefore = 0
                    $para.ParagraphFormat.SpaceAfter = 4
                }
            }
        }
    }
}

# 5. Slide 19: Apply literal hyphen "- " prefix
if (19 -le $pres.Slides.Count) {
    $s19 = $pres.Slides.Item(19)
    foreach ($sh in $s19.Shapes) {
        if ($sh.HasTextFrame -eq -1 -and $sh.Top -gt 50 -and $sh.Top -lt 300) {
            $tf = $sh.TextFrame
            if ($tf.HasText -eq -1) {
                for ($p = $tf.TextRange.Paragraphs().Count; $p -ge 1; $p--) {
                    $para = $tf.TextRange.Paragraphs($p)
                    $trimmed = $para.Text.Trim()
                    if ($trimmed -eq "" -or $trimmed -eq "0" -or $trimmed -eq "-") {
                        if ($tf.TextRange.Paragraphs().Count -gt 1) {
                            $para.Delete()
                        }
                    }
                }
                for ($p = 1; $p -le $tf.TextRange.Paragraphs().Count; $p++) {
                    $para = $tf.TextRange.Paragraphs($p)
                    $para.ParagraphFormat.Bullet.Type = 0
                    $para.ParagraphFormat.Bullet.Visible = 0
                    if ($para.Text.StartsWith("- ") -or $para.Text.StartsWith("0 ") -or $para.Text.StartsWith("0`t") -or $para.Text.StartsWith([string][char]8226 + " ")) {
                        $para.Characters(1, 2).Delete()
                    } elseif ($para.Text.StartsWith([string][char]8226) -or $para.Text.StartsWith("0") -or $para.Text.StartsWith("-")) {
                        $para.Characters(1, 1).Delete()
                    }
                    if (-not $para.Text.StartsWith("- ")) {
                        $ins = $para.InsertBefore("- ")
                        $ins.Font.Name = "Arial"
                        $ins.Font.Bold = 0
                    }
                    $para.Font.Name = "Arial"
                    $para.ParagraphFormat.SpaceBefore = 0
                    $para.ParagraphFormat.SpaceAfter = 6
                }
            }
        }
    }
}

# 6. Slide 11: Table 'Bộ luật hậu xử lý' - format text with Arial so 'O' (capital letter) and '0' (digit zero) are distinct
if (11 -le $pres.Slides.Count) {
    $s11 = $pres.Slides.Item(11)
    foreach ($sh in $s11.Shapes) {
        if ($sh.HasTable -eq -1) {
            $tbl = $sh.Table
            for ($r = 1; $r -le $tbl.Rows.Count; $r++) {
                for ($c = 1; $c -le $tbl.Columns.Count; $c++) {
                    $tr = $tbl.Cell($r, $c).Shape.TextFrame.TextRange
                    $tr.Font.Name = "Arial"
                }
            }
            if ($tbl.Rows.Count -ge 5) {
                $c2 = $tbl.Cell(5, 2).Shape.TextFrame.TextRange
                $c2.Text = "O " + [char]8594 + " 0 hợp lý, 0 " + [char]8594 + " O không bao giờ — chiều đúng là 0 " + [char]8594 + " D"
                $c2.Font.Name = "Arial"
                $c2.Font.Size = 13
            }
        }
    }
}

# 7. Slide 21: Table 'Hướng phát triển' - 6 distinct rows, synchronized with Table 5.3 in thesis
if (21 -le $pres.Slides.Count) {
    $slide21 = $pres.Slides.Item(21)
    foreach ($sh in $slide21.Shapes) {
        if ($sh.HasTable -eq -1) {
            $tbl = $sh.Table
            if ($tbl.Rows.Count -ge 7) {
                # Column 3 values: 1, 1, 3, 4, 2, 5, —, —
                $col3Vals = @("1", "1", "3, 4", "2, 5", [string][char]8212, [string][char]8212)
                for ($r = 1; $r -le 6; $r++) {
                    $rowIdx = $r + 1
                    $c1 = $tbl.Cell($rowIdx, 1).Shape.TextFrame.TextRange
                    $c2 = $tbl.Cell($rowIdx, 2).Shape.TextFrame.TextRange
                    $c3 = $tbl.Cell($rowIdx, 3).Shape.TextFrame.TextRange
                    
                    $c1.Font.Name = "Arial"; $c1.Font.Size = 12
                    $c2.Font.Name = "Arial"; $c2.Font.Size = 12
                    $c3.Font.Name = "Arial"; $c3.Font.Size = 12
                    
                    $c1.ParagraphFormat.Alignment = 2 # center
                    $c2.ParagraphFormat.Alignment = 1 # left
                    
                    $c3.Text = $col3Vals[$r - 1]
                    $c3.Font.Name = "Arial"
                    $c3.Font.Size = 12
                    $c3.ParagraphFormat.Alignment = 2 # center
                }
            }
        }
    }
}

# 8. Slide 9, 11, 17: Thoroughly remove any extraneous overlapping shapes at bottom margin
# Slide 9: Exactly 1 Picture (pipeline strip). Delete any extra picture or shape below y=330.
if (9 -le $pres.Slides.Count) {
    $s9 = $pres.Slides.Item(9)
    $picCount = 0
    for ($i = $s9.Shapes.Count; $i -ge 1; $i--) {
        $sh = $s9.Shapes.Item($i)
        $isPageNum = ($sh.Width -lt 50 -and $sh.Height -lt 50 -and $sh.Left -lt 50)
        if (-not $isPageNum) {
            if ($sh.Type -eq 13 -or $sh.Name -like "*Picture*") {
                $picCount++
                if ($picCount -gt 1) {
                    $sh.Delete()
                }
            } elseif ($sh.Top -gt 450 -or ($sh.Top + $sh.Height) -gt 530) {
                $sh.Delete()
            }
        }
    }
}

# Slide 11: Has a table, MUST NOT have ANY picture shape.
if (11 -le $pres.Slides.Count) {
    $s11 = $pres.Slides.Item(11)
    for ($i = $s11.Shapes.Count; $i -ge 1; $i--) {
        $sh = $s11.Shapes.Item($i)
        $isPageNum = ($sh.Width -lt 50 -and $sh.Height -lt 50 -and $sh.Left -lt 50)
        if (-not $isPageNum) {
            if ($sh.Type -eq 13 -or $sh.Name -like "*Picture*") {
                $sh.Delete()
            } elseif ($sh.Top -gt 460 -and -not $sh.HasTable) {
                $sh.Delete()
            }
        }
    }
}

# Slide 17: Exactly 1 Picture (4 metric cards). Delete any extra picture or shape below.
if (17 -le $pres.Slides.Count) {
    $s17 = $pres.Slides.Item(17)
    $picCount = 0
    for ($i = $s17.Shapes.Count; $i -ge 1; $i--) {
        $sh = $s17.Shapes.Item($i)
        $isPageNum = ($sh.Width -lt 50 -and $sh.Height -lt 50 -and $sh.Left -lt 50)
        if (-not $isPageNum) {
            if ($sh.Type -eq 13 -or $sh.Name -like "*Picture*") {
                $picCount++
                if ($picCount -gt 1) {
                    $sh.Delete()
                }
            } elseif ($sh.Top -gt 450 -or ($sh.Top + $sh.Height) -gt 530) {
                $sh.Delete()
            }
        }
    }
}

# 9. Slide 22: Ensure clean 'Kết luận chung' without any stray '0' or blank line; pull up close to title
if (22 -le $pres.Slides.Count) {
    $s22 = $pres.Slides.Item(22)
    for ($i = $s22.Shapes.Count; $i -ge 1; $i--) {
        $sh = $s22.Shapes.Item($i)
        if ($sh.HasTextFrame -eq -1) {
            $txt = $sh.TextFrame.TextRange.Text.Trim()
            if (($txt -eq "0" -or $txt -eq "") -and $sh.Width -gt 50 -and $sh.Top -lt 100) {
                $sh.Delete()
                continue
            }
            if ($sh.Top -gt 50 -and $sh.Top -lt 300) {
                # Pull shape slightly closer to title
                $sh.Top = 85
                $tf = $sh.TextFrame
                
                # Delete empty or lone '0' or '-' paragraphs
                for ($p = $tf.TextRange.Paragraphs().Count; $p -ge 1; $p--) {
                    $para = $tf.TextRange.Paragraphs($p)
                    $trimmed = $para.Text.Trim()
                    if ($trimmed -eq "0" -or $trimmed -eq "" -or $trimmed -eq "-" -or $trimmed -eq [string][char]8211) {
                        if ($tf.TextRange.Paragraphs().Count -gt 1) {
                            $para.Delete()
                        }
                    }
                }
                
                # Format each of the 4 paragraphs with literal "- " and Bullet.Type = 0
                for ($p = 1; $p -le $tf.TextRange.Paragraphs().Count; $p++) {
                    $para = $tf.TextRange.Paragraphs($p)
                    $para.ParagraphFormat.Bullet.Type = 0
                    $para.ParagraphFormat.Bullet.Visible = 0
                    
                    if ($para.Text.StartsWith("- ") -or $para.Text.StartsWith("0 ") -or $para.Text.StartsWith("0`t") -or $para.Text.StartsWith([string][char]8226 + " ")) {
                        $para.Characters(1, 2).Delete()
                    } elseif ($para.Text.StartsWith([string][char]8226) -or $para.Text.StartsWith("0") -or $para.Text.StartsWith("-")) {
                        $para.Characters(1, 1).Delete()
                    }
                    
                    if (-not $para.Text.StartsWith("- ")) {
                        $ins = $para.InsertBefore("- ")
                        $ins.Font.Name = "Arial"
                        $ins.Font.Bold = 0
                    }
                    
                    $para.Font.Name = "Arial"
                    $para.ParagraphFormat.SpaceBefore = 0
                    $para.ParagraphFormat.SpaceAfter = 8
                }
            }
        }
    }
}

# 10. Slide 23: Format as a prestigious, centered Thank You & Q&A slide with pipe separator between student names
if (23 -le $pres.Slides.Count) {
    $s23 = $pres.Slides.Item(23)
    foreach ($sh in $s23.Shapes) {
        if ($sh.HasTextFrame -eq -1 -and $sh.Top -gt 70 -and $sh.Top -lt 200) {
            $tf = $sh.TextFrame
            for ($p = 1; $p -le $tf.TextRange.Paragraphs().Count; $p++) {
                $para = $tf.TextRange.Paragraphs($p)
                $para.ParagraphFormat.Bullet.Type = 0
                $para.ParagraphFormat.Alignment = 2 # Center
            }
            if ($tf.TextRange.Paragraphs().Count -ge 5) {
                $p1 = $tf.TextRange.Paragraphs(1)
                $p1.Font.Size = 19
                $p1.Font.Bold = -1
                $p1.Font.Color.RGB = 0x803300 # Dark Navy/Blue
                $p1.ParagraphFormat.SpaceBefore = 10
                $p1.ParagraphFormat.SpaceAfter = 18

                $p2 = $tf.TextRange.Paragraphs(2)
                $p2.Font.Size = 15
                $p2.Font.Bold = 0
                $p2.ParagraphFormat.SpaceAfter = 8

                $p3 = $tf.TextRange.Paragraphs(3)
                $p3.Text = "Sinh viên thực hiện: Phạm Nguyễn Thế Châu | Nguyễn Công Hậu | Nguyễn Minh Hiếu | Phạm Công Thành"
                $p3.Font.Size = 14
                $p3.Font.Name = "Arial"
                $p3.Font.Bold = 0
                $p3.ParagraphFormat.SpaceAfter = 24

                $p4 = $tf.TextRange.Paragraphs(4)
                $p4.Font.Size = 17
                $p4.Font.Bold = -1
                $p4.Font.Italic = -1
                $p4.Font.Color.RGB = 0x222222
                $p4.ParagraphFormat.SpaceAfter = 16

                $p5 = $tf.TextRange.Paragraphs(5)
                $p5.Font.Size = 24
                $p5.Font.Bold = -1
                $p5.Font.Color.RGB = 0xCC6600 # Accent Blue
                $p5.ParagraphFormat.SpaceBefore = 10
            }
        }
    }
}

$pres.Save()

# Export primary PDF
$pdfPath = [System.IO.Path]::ChangeExtension($fullPath, ".pdf")
$pres.SaveAs($pdfPath, 32)
Write-Output "Exported PDF: $pdfPath"

$pres.Close()
$ppt.Quit()

# Also ensure delivery copies in nop/ and D:\baocao_damh:
# - 02-slide-mon-hoc.pptx & .pdf
# - 02-slide-mon-hoc_FINAL.pptx & .pdf
$nopDir = "D:\DATN\nop"
$damhDir = "D:\baocao_damh"

if (Test-Path $nopDir) {
    Copy-Item -Path $fullPath -Destination (Join-Path $nopDir "02-slide-mon-hoc.pptx") -Force
    Copy-Item -Path $pdfPath -Destination (Join-Path $nopDir "02-slide-mon-hoc.pdf") -Force
}

if (Test-Path $damhDir) {
    Copy-Item -Path $fullPath -Destination (Join-Path $damhDir "02-slide-mon-hoc.pptx") -Force
    Copy-Item -Path $pdfPath -Destination (Join-Path $damhDir "02-slide-mon-hoc.pdf") -Force
}

Write-Output "Successfully patched Slide 8 title, literal hyphen bullets on S3/S19/S22, Slide 11 O vs 0, Slide 21 table, S9/S11/S17 bottom images, Slide 22, and Slide 23."
