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

# 3. Bullet Normalization:
# Only Slide 3, 19, 22 are bullet slides. Other slides have lead sentences without bullets.
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
        continue
    }
    
    # Process bullet slides: Slide 3, 19, 22
    foreach ($sh in $slide.Shapes) {
        if ($sh.HasTextFrame -eq -1 -and $sh.Top -gt 50 -and $sh.Top -lt 300) {
            $tf = $sh.TextFrame
            if ($tf.HasText -eq -1) {
                # Delete empty or stray '0' or lone '-' paragraphs from bottom to top
                for ($p = $tf.TextRange.Paragraphs().Count; $p -ge 1; $p--) {
                    $para = $tf.TextRange.Paragraphs($p)
                    $trimmed = $para.Text.Trim()
                    if ($trimmed -eq "" -or $trimmed -eq "0" -or $trimmed -eq "-" -or $trimmed -eq [string][char]8211 -or $trimmed -eq [string][char]8212) {
                        if ($tf.TextRange.Paragraphs().Count -gt 1) {
                            $para.Delete()
                        }
                    }
                }
                
                # Format each paragraph
                for ($p = 1; $p -le $tf.TextRange.Paragraphs().Count; $p++) {
                    $para = $tf.TextRange.Paragraphs($p)
                    # Strip any manual leading dash or bullet prefix while keeping remaining bold runs
                    if ($para.Text.StartsWith("- ") -or $para.Text.StartsWith("0 ") -or $para.Text.StartsWith("0`t")) {
                        $para.Characters(1, 2).Delete()
                    } elseif ($para.Text.StartsWith([string][char]8226 + " ")) {
                        $para.Characters(1, 2).Delete()
                    } elseif ($para.Text.StartsWith([string][char]8226)) {
                        $para.Characters(1, 1).Delete()
                    }
                    
                    # Apply clean standard bullet
                    $para.ParagraphFormat.Bullet.Type = 1 # ppBulletUnnumbered
                    $para.ParagraphFormat.Bullet.Character = 8226 # solid circle
                    $para.ParagraphFormat.Bullet.Font.Name = "Arial"
                    $para.ParagraphFormat.Bullet.Visible = -1
                    $para.Font.Name = "Arial"
                }
            }
        }
    }
}

# 4. Slide 11: Table 'Bộ luật hậu xử lý' - format text with Arial so 'O' (capital letter) and '0' (digit zero) are distinct
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

# 5. Slide 21: Table 'Hướng phát triển' - 6 distinct rows, synchronized with Table 5.3 in thesis
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

# 6. Slide 9, 11, 17: Thoroughly remove any extraneous overlapping shapes at bottom margin
foreach ($sIdx in @(9, 11, 17)) {
    if ($sIdx -le $pres.Slides.Count) {
        $slide = $pres.Slides.Item($sIdx)
        for ($i = $slide.Shapes.Count; $i -ge 1; $i--) {
            $sh = $slide.Shapes.Item($i)
            $isPageNum = ($sh.Width -lt 50 -and $sh.Height -lt 50 -and $sh.Left -lt 50)
            if (-not $isPageNum) {
                # Slide 11 has a table, MUST NOT have any picture
                if ($sIdx -eq 11 -and ($sh.Type -eq 13 -or $sh.Name -like "*Picture*")) {
                    $sh.Delete()
                    continue
                }
                # Slide 9 and 17 have a single main figure. Any extra shape protruding near bottom must be removed
                if ($sh.Top -gt 450 -or ($sh.Top + $sh.Height) -gt 530) {
                    $sh.Delete()
                }
            }
        }
    }
}

# 7. Slide 22: Ensure clean 'Kết luận chung' without any stray characters or isolated 0
if (22 -le $pres.Slides.Count) {
    $s22 = $pres.Slides.Item(22)
    for ($i = $s22.Shapes.Count; $i -ge 1; $i--) {
        $sh = $s22.Shapes.Item($i)
        if ($sh.HasTextFrame -eq -1) {
            $txt = $sh.TextFrame.TextRange.Text.Trim()
            if (($txt -eq "0" -or $txt -eq "") -and $sh.Width -gt 50) {
                $sh.Delete()
                continue
            }
            $tf = $sh.TextFrame
            for ($p = $tf.TextRange.Paragraphs().Count; $p -ge 1; $p--) {
                $para = $tf.TextRange.Paragraphs($p)
                $trimmed = $para.Text.Trim()
                if ($trimmed -eq "0" -or $trimmed -eq "" -or $trimmed -eq "-" -or $trimmed -eq [string][char]8211) {
                    if ($tf.TextRange.Paragraphs().Count -gt 1) {
                        $para.Delete()
                    }
                }
            }
        }
    }
}

# 8. Slide 23: Format as a prestigious, centered Thank You & Q&A slide with pipe separator between student names
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

# Automatically export to PDF
$pdfPath = [System.IO.Path]::ChangeExtension($fullPath, ".pdf")
$pres.SaveAs($pdfPath, 32)
Write-Output "Exported PDF: $pdfPath"

$pres.Close()
$ppt.Quit()
Write-Output "Successfully patched Slide 8 title, slide bullets, Slide 3 bullets, Slide 11 O vs 0, Slide 21 table, Slide 22, and Slide 23 in $DeckPath"
