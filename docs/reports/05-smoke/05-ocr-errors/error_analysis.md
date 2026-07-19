# Phan tich loi OCR

- Bao cao nguon sinh luc: `2026-07-19T13:16:57+00:00`
- Engine: `paddleocr-PP-OCRv5-mobile(det=PP-OCRv5_mobile_det)`
- Chuoi duoc phan tich: `normalized`
- Tong so mau: **60**, so mau sai: **21** (35.0%)

## 1. Phan bo theo loai loi

| Loai loi | So mau | Ty le |
|---|---|---|
| `correct` | 39 | 65.0% |
| `empty_read` | 0 | 0.0% |
| `substitution` | 8 | 13.3% |
| `missing_chars` | 4 | 6.7% |
| `extra_chars` | 2 | 3.3% |
| `transposition` | 0 | 0.0% |
| `mixed` | 7 | 11.7% |

## 2. Phan bo theo so dong

| Loai loi | Bien 1 dong | Bien 2 dong |
|---|---|---|
| **Tong so mau** | 10 | 50 |
| `correct` | 10 | 29 |
| `empty_read` | 0 | 0 |
| `substitution` | 0 | 8 |
| `missing_chars` | 0 | 4 |
| `extra_chars` | 0 | 2 |
| `transposition` | 0 | 0 |
| `mixed` | 0 | 7 |

## 3. Cac cap ky tu bi nham nhieu nhat

| That | Doc thanh | So lan |
|---|---|---|
| `U` | `1` | 2 |
| `E` | `F` | 2 |
| `N` | `M` | 1 |
| `4` | `A` | 1 |
| `0` | `U` | 1 |
| `5` | `9` | 1 |
| `H` | `M` | 1 |
| `U` | `D` | 1 |
| `6` | `5` | 1 |
| `1` | `8` | 1 |
| `6` | `G` | 1 |
| `5` | `8` | 1 |
| `4` | `L` | 1 |

## 4. Vi tri ky tu hay sai

| Vi tri (0-based) | So lan sai |
|---|---|
| 0 | 10 |
| 1 | 9 |
| 2 | 14 |
| 3 | 7 |
| 4 | 2 |
| 6 | 1 |
| 7 | 1 |

## 5. Sai nhung do tin cay cao

Day la kieu loi nguy hiem nhat: he thong sai ma van tu tin, nen khong
the dung nguong do tin cay de loc bo.

| Do tin cay | That | Doc thanh | Loai loi |
|---|---|---|---|
| 1.000 | `59U172979` | `72979` | `missing_chars` |
| 0.998 | `71H15511` | `5518` | `mixed` |
| 0.997 | `78N25203` | `5203` | `missing_chars` |
| 0.994 | `55P48426` | `55PL8426` | `substitution` |
| 0.992 | `30A21624` | `21624` | `missing_chars` |
| 0.992 | `63B703323` | `63B7U3323` | `substitution` |
| 0.990 | `59C113183` | `13183` | `missing_chars` |
| 0.985 | `59H167791` | `H1G7791` | `mixed` |
| 0.984 | `55E121500` | `59F121500` | `substitution` |
| 0.962 | `59U139997` | `59D139997` | `substitution` |
| 0.955 | `59U170392` | `5911170392` | `mixed` |
| 0.947 | `59T188808` | `59T188808J91` | `extra_chars` |
| 0.929 | `59H121704` | `59M121704` | `substitution` |
| 0.928 | `59N147102` | `59M147102` | `substitution` |
| 0.918 | `59S227831` | `59S227831J9` | `extra_chars` |
| 0.898 | `60B422155` | `50B422155` | `substitution` |
| 0.896 | `59U109278` | `5911109278` | `mixed` |
| 0.862 | `30E66971` | `30F66971` | `substitution` |
| 0.844 | `55F114927` | `85F11492765R1` | `mixed` |
| 0.826 | `59F170424` | `70A2419P` | `mixed` |
