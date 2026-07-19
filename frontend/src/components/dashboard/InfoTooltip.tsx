/**
 * Small "what does this number mean?" tooltip.
 *
 * Exists mainly for one distinction. The dashboard shows uploads and license
 * plates side by side, and the two are easy to confuse — an image holding three
 * plates counts as one upload and three plates. A short label cannot carry that
 * explanation, and a permanent paragraph under every tile would drown the
 * figures it is meant to clarify.
 */

import { useEffect, useId, useState } from 'react';
import { Info } from 'lucide-react';

/** Props of {@link InfoTooltip}. */
export interface InfoTooltipProps {
  /**
   * What the button is, for assistive technology, e.g.
   * `"Giải thích: Lượt nhận dạng"`. The icon alone conveys nothing.
   */
  label: string;
  /** The explanation itself, in Vietnamese. */
  text: string;
}

/**
 * Render an info icon that reveals an explanation.
 *
 * Opens on hover *and* on focus, and is a real `<button>`, so the content is
 * reachable by keyboard and by touch rather than by pointer alone. While open
 * it is wired to the trigger with `aria-describedby`, which is what makes a
 * screen reader announce the explanation as part of the control instead of as
 * stray text.
 *
 * @param props - Accessible label and explanation text.
 * @returns The trigger, with its tooltip when open.
 */
export function InfoTooltip({ label, text }: InfoTooltipProps): JSX.Element {
  const tooltipId = useId();

  /*
   * Three independent reasons to be open, rather than one boolean.
   *
   * A single flag toggled by every handler breaks on the most ordinary
   * interaction there is: hovering opens the tooltip, and the click that
   * follows toggles the same flag back off, so the explanation disappears at
   * the exact moment the user asks for it. Keeping "pointer is over it",
   * "keyboard is on it" and "the user clicked to keep it" apart means a click
   * pins the tooltip open instead of fighting the hover that preceded it.
   */
  const [isHovered, setIsHovered] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [isPinned, setIsPinned] = useState(false);

  const isOpen = isHovered || isFocused || isPinned;

  // Escape closes the tooltip, matching what a keyboard user expects of any
  // transient overlay. Bound only while open so the dashboard is not listening
  // on every keystroke for a tooltip nobody has opened.
  useEffect(() => {
    if (!isOpen) {
      return;
    }
    const handleKeyDown = (event: KeyboardEvent): void => {
      if (event.key === 'Escape') {
        // Every reason to be open is cleared, focus included. The ARIA practice
        // for tooltips is that Escape dismisses regardless of what opened it;
        // leaving the focus flag set would keep the tooltip on screen and make
        // the key look broken to the one user who most needs it. Tabbing away
        // and back fires `focus` again, so the tooltip is not lost for good.
        setIsPinned(false);
        setIsHovered(false);
        setIsFocused(false);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  return (
    <span className="relative inline-flex align-middle">
      <button
        type="button"
        aria-label={label}
        aria-expanded={isOpen}
        aria-describedby={isOpen ? tooltipId : undefined}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        // Pinning is what makes the tooltip usable on a touch screen, where no
        // hover event ever arrives.
        onClick={() => setIsPinned((previous) => !previous)}
        className="inline-flex h-4 w-4 items-center justify-center rounded-full
                   text-content-muted transition-colors hover:text-content"
      >
        <Info className="h-3.5 w-3.5" aria-hidden="true" />
      </button>

      {isOpen && (
        <span
          role="tooltip"
          id={tooltipId}
          className="absolute bottom-full left-1/2 z-30 mb-2 w-56 -translate-x-1/2
                     rounded-lg border border-border bg-surface p-2.5
                     text-xs font-normal leading-relaxed text-content shadow-lg"
        >
          {text}
        </span>
      )}
    </span>
  );
}

export default InfoTooltip;
