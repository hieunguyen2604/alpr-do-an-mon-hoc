/** Map plate family + background colour to user-facing Vietnamese badges. */

/** Plate family inferred from the character string, as returned by the API. */
export type PlateKind =
  | 'car'
  | 'motorcycle_new'
  | 'motorcycle_old'
  | 'blue_car'
  | 'blue_motorcycle'
  | 'special'
  | 'diplomatic'
  | 'military'
  | 'unknown';

/** Plate background colour read from the crop, as returned by the API. */
export type PlateColor = 'white' | 'yellow' | 'blue' | 'red' | 'unknown';

/** How a badge should be styled. Mirrors the `Badge` component's variants. */
export type BadgeTone = 'success' | 'warning' | 'neutral' | 'info';

/** A badge to render for one detected plate. */
export interface PlateClassBadge {
  /** Text shown to the user. Vietnamese, and meaningful without the colour. */
  label: string;
  /** Visual tone. Never the sole carrier of meaning (NFR-U5). */
  tone: BadgeTone;
  /** Longer explanation, shown on hover. */
  title: string;
}

const COLOR_LABELS: Record<PlateColor, string> = {
  white: 'Nền trắng',
  yellow: 'Nền vàng',
  blue: 'Nền xanh',
  red: 'Nền đỏ',
  unknown: 'Màu nền không xác định',
};

const COLOR_MEANING: Record<PlateColor, string> = {
  white: 'Cá nhân, doanh nghiệp, tổ chức trong nước',
  yellow: 'Xe kinh doanh vận tải — taxi, xe tải, xe khách, xe công nghệ',
  blue: 'Cơ quan Đảng, Nhà nước, tổ chức chính trị - xã hội, đơn vị sự nghiệp công lập',
  red: 'Xe Quân đội',
  unknown: 'Không đọc được màu nền từ ảnh đã cắt',
};

/** Describe the plate family in Vietnamese; returns null for unknown kind. */
function describeKind(kind: PlateKind | null, color: PlateColor | null): string | null {
  switch (kind) {
    case 'military':
      return 'Biển quân đội';
    case 'diplomatic':
      return 'Biển ngoại giao';
    case 'blue_car':
      return 'Ô tô cơ quan nhà nước';
    case 'blue_motorcycle':
      return 'Xe máy cơ quan nhà nước';
    case 'special':
      return 'Biển chuyên dùng';
    case 'car':
      // Distinguish commercial transport vehicle by yellow plate color
      return color === 'yellow' ? 'Ô tô kinh doanh vận tải' : 'Ô tô';
    case 'motorcycle_new':
    case 'motorcycle_old':
      return color === 'yellow' ? 'Xe máy kinh doanh vận tải' : 'Xe máy';
    default:
      return null;
  }
}

/** Build badges shown next to a recognised plate. */
export function plateClassBadges(
  isValidFormat: boolean,
  kind: PlateKind | null | undefined,
  color: PlateColor | null | undefined,
): PlateClassBadge[] {
  const badges: PlateClassBadge[] = [];
  const description = describeKind(kind ?? null, color ?? null);

  if (description !== null) {
    badges.push({
      label: description,
      tone: 'info',
      title: `Loại biển suy ra từ chuỗi ký tự (${kind})`,
    });
  }

  if (color && color !== 'unknown') {
    badges.push({
      label: COLOR_LABELS[color],
      tone: 'neutral',
      title: COLOR_MEANING[color],
    });
  }

  // Military/diplomatic plates are non-civil registry rather than invalid format
  const outsideCivilRegistry = kind === 'military' || kind === 'diplomatic';

  if (!isValidFormat) {
    if (outsideCivilRegistry) {
      badges.push({
        label: 'Ngoài hệ đăng ký dân sự',
        tone: 'neutral',
        title:
          'Biển này không thuộc hệ thống đăng ký dân sự nên không đối chiếu ' +
          'được với các định dạng dân sự — đây không phải lỗi đọc.',
      });
    } else {
      badges.push({
        label: 'Sai định dạng biển số',
        tone: 'warning',
        title: 'Chuỗi đọc được không khớp định dạng biển số Việt Nam nào',
      });
    }
  }


  return badges;
}
