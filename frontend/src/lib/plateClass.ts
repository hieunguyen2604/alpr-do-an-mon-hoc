/**
 * Turn a plate's family and background colour into what a user should read.
 *
 * The problem this solves
 * -----------------------
 * The interface used to show one of two badges: "Đúng định dạng biển số" or
 * "Sai định dạng biển số", driven by `is_valid_format` alone. That flag means
 * "matches a **civil** Vietnamese layout", so an army plate — read perfectly, at
 * 0.999 OCR confidence — was shown to the user as a *wrong format*. It is not
 * wrong; it simply sits outside the civil registration system. Presenting a
 * correct reading as a failure is worse than showing nothing, because it teaches
 * the operator to distrust results that are in fact right.
 *
 * Why two inputs
 * --------------
 * Neither field identifies a vehicle class on its own, and the gaps do not
 * overlap:
 *
 * - `plate_kind` reads the character string, so it cannot see that a commercial
 *   vehicle's yellow plate carries the same layout as a private vehicle's white
 *   one. Both report `car`.
 * - `plate_color` reads the pixels, so it cannot tell a diplomatic plate from a
 *   private one. Both are white.
 *
 * Combined, they cover every row of the table in Circular 79/2024/TT-BCA.
 */

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

/**
 * Describe the plate family in words a defence panel would accept.
 *
 * @param kind - Family from the character string.
 * @param color - Background colour from the crop.
 * @returns A human description, or `null` when the family is unknown — in which
 *   case the caller falls back to the plain format verdict rather than showing
 *   an empty badge.
 */
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
      // The one distinction neither the string nor the backend can settle. A
      // blue plate is already promoted to `blue_car` by the pipeline, because
      // blue is unambiguous evidence; yellow is not, because a yellow plate and
      // a white one are the *same* family — only the vehicle's use differs.
      return color === 'yellow' ? 'Ô tô kinh doanh vận tải' : 'Ô tô';
    case 'motorcycle_new':
    case 'motorcycle_old':
      return color === 'yellow' ? 'Xe máy kinh doanh vận tải' : 'Xe máy';
    default:
      return null;
  }
}

/**
 * Build the badges shown next to a recognised plate.
 *
 * @param isValidFormat - Whether the string matches a civil Vietnamese layout.
 * @param kind - Plate family from the API, if recorded.
 * @param color - Background colour from the API, if recorded.
 * @returns Badges in display order: what the plate *is* first, then whether the
 *   string parsed. Records stored before this feature existed carry neither
 *   field, so the result degrades to the original single verdict rather than
 *   showing a blank.
 */
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

  // An army or diplomatic plate is a real plate that deliberately fails civil
  // validation. Saying "wrong format" there would contradict the badge beside
  // it, so the wording changes to state the actual relationship.
  const outsideCivilRegistry = kind === 'military' || kind === 'diplomatic';

  if (isValidFormat) {
    badges.push({
      label: 'Đúng định dạng biển số',
      tone: 'success',
      title: 'Chuỗi khớp một định dạng biển số dân sự Việt Nam',
    });
  } else if (outsideCivilRegistry) {
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

  return badges;
}
