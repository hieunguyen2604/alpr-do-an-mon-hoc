/**
 * Resolve the design tokens that charts need as concrete colour strings.
 *
 * Recharts paints through SVG `stroke` and `fill`, and its tooltip and legend
 * take inline style objects. Neither reliably accepts a bare `var(--token)`
 * across every browser the project targets, and the tooltip styles are plain
 * CSS objects where a custom property would have to be resolved anyway. So the
 * values are read once from the cascade and handed over as `rgb(...)` strings.
 *
 * Reading them rather than hard-coding them is the point: `index.css` stays the
 * single source of truth for the palette, and a token edit reaches the charts
 * without a matching edit here.
 */

import { useEffect, useState } from 'react';

/** Colours a chart needs, already resolved to `rgb(...)` strings. */
export interface ChartTheme {
  /** Series colour for uploads (`job_count`). */
  jobs: string;
  /** Series colour for recognised plates (`detection_count`). */
  plates: string;
  /** Hairline gridlines, one shade off the surface. */
  grid: string;
  /** Axis lines and tick labels. */
  axis: string;
  /** Tooltip background. */
  surface: string;
  /** Tooltip border. */
  border: string;
  /** Tooltip body text. */
  text: string;
}

/**
 * Token names backing each entry of {@link ChartTheme}.
 *
 * Kept beside the fallbacks so the two lists cannot drift apart.
 */
const TOKENS: Readonly<Record<keyof ChartTheme, string>> = {
  jobs: '--chart-jobs',
  plates: '--chart-plates',
  grid: '--color-border',
  axis: '--color-text-muted',
  surface: '--color-surface',
  border: '--color-border',
  text: '--color-text',
};

/**
 * Light-theme values, used before the first read and if a token is missing.
 *
 * These duplicate the `:root` block of `index.css` on purpose: a chart that
 * renders during the first paint, or in a test environment without stylesheets,
 * still draws something legible instead of black-on-black.
 */
const FALLBACK_THEME: ChartTheme = {
  jobs: 'rgb(37 99 235)',
  plates: 'rgb(22 163 74)',
  grid: 'rgb(226 232 240)',
  axis: 'rgb(100 116 139)',
  surface: 'rgb(255 255 255)',
  border: 'rgb(226 232 240)',
  text: 'rgb(15 23 42)',
};

/**
 * Read the current value of every chart token from the document.
 *
 * Tokens hold bare RGB channel triplets ("37 99 235") rather than complete
 * colours, because Tailwind needs that form to build `bg-primary/10`. They are
 * wrapped into `rgb(...)` here, which is what SVG and inline styles expect.
 *
 * @returns The resolved theme, or the light fallback outside a browser.
 */
function readChartTheme(): ChartTheme {
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return FALLBACK_THEME;
  }

  const styles = window.getComputedStyle(document.documentElement);

  /**
   * Resolve one token, falling back when it is absent or empty.
   *
   * @param key - Which chart colour to resolve.
   * @returns A usable `rgb(...)` string.
   */
  const resolve = (key: keyof ChartTheme): string => {
    const channels = styles.getPropertyValue(TOKENS[key]).trim();
    return channels ? `rgb(${channels})` : FALLBACK_THEME[key];
  };

  return {
    jobs: resolve('jobs'),
    plates: resolve('plates'),
    grid: resolve('grid'),
    axis: resolve('axis'),
    surface: resolve('surface'),
    border: resolve('border'),
    text: resolve('text'),
  };
}

/**
 * Subscribe to the chart palette, re-resolving it when the theme changes.
 *
 * Tailwind is configured with `darkMode: 'class'`, so switching themes toggles a
 * class on an ancestor element rather than firing any event. A `MutationObserver`
 * on the `class` attribute is therefore the only way to notice: without it the
 * charts would keep their light-theme colours on a dark surface, which is
 * exactly the low-contrast failure the tokens exist to prevent.
 *
 * Both `<html>` and `<body>` are watched because either is a conventional place
 * to hang the `dark` class, and this hook should not dictate which one a future
 * theme toggle picks.
 *
 * @returns The colours to hand to Recharts, current for the active theme.
 */
export function useChartTheme(): ChartTheme {
  const [theme, setTheme] = useState<ChartTheme>(readChartTheme);

  useEffect(() => {
    // Re-read after mount: the first render may have run before the stylesheet
    // was applied, in which case the initial state holds the fallback.
    setTheme(readChartTheme());

    const observer = new MutationObserver(() => {
      setTheme(readChartTheme());
    });

    for (const target of [document.documentElement, document.body]) {
      observer.observe(target, {
        attributes: true,
        attributeFilter: ['class'],
      });
    }

    return () => observer.disconnect();
  }, []);

  return theme;
}

/**
 * Vietnamese labels for the two measures every dashboard chart plots.
 *
 * Shared by the charts and their table views so a legend, an axis and a column
 * heading cannot disagree about what a series is called.
 *
 * The wording is the whole point of these constants. The API reports
 * `total_jobs` (uploads) and `total_detections` (license plates) as separate
 * figures, and one image holding three plates is one upload and three plates.
 * Labelling both "số lượt" would merge two different quantities into one
 * plausible-looking, wrong number.
 */
export const SERIES_LABELS = {
  /** Uploads — one per file submitted, whatever it contained. */
  jobs: 'Lượt nhận dạng',
  /** License plates — several may come from a single upload. */
  plates: 'Biển số phát hiện',
} as const;
