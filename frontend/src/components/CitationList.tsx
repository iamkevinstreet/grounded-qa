// ########################################################################
// #               frontend/src/components/CitationList.tsx               #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The numbered list of checked citations; choosing one shows its
 * passage.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Local
import { sectionLabel } from '../labels';
import { required } from '../lib/required';
import type { Citation } from '../types';

// ########################################################################
// #                            Citation list                             #
// ########################################################################
interface Props {
  citations?: Citation[] | null;
  selected?: number | null;
  onSelect?: ((n: number) => void) | null;
}

// log.debug('Defines the citation list')
/**
 * Renders the numbered list of checked citations.
 *
 * @param props - The component's props.
 * @param props.citations - The checked citations, in number order.
 *   Required.
 * @param props.selected - The number of the citation the sheet shows.
 *   Required.
 * @param props.onSelect - Shows a citation, by its number. Required.
 * @returns The list, one button per citation.
 */
export function CitationList({
  citations = null,
  selected = null,
  onSelect = null,
}: Props = {}): React.JSX.Element {
  // log.debug('Takes the citations, which the caller must give')
  citations = required({ citations });
  // log.debug('Takes the citation shown, which the caller must give')
  selected = required({ selected });
  // log.debug('Takes what choosing a citation does, which the caller must give')
  onSelect = required({ onSelect });
  // log.debug('Returns one button per citation, in number order')
  return (
    <ol className="gq-cites" aria-label="Sources for this answer">
      {citations.map((citation) => (
        <li key={citation.n}>
          <button
            className="gq-cite"
            type="button"
            aria-pressed={citation.n === selected}
            onClick={() => onSelect(citation.n)}
          >
            <span className="gq-cite__n">{citation.n}</span>
            <span className="gq-cite__title">{citation.title}</span>
            <span className="gq-cite__section">{sectionLabel(citation.section)}</span>
          </button>
        </li>
      ))}
    </ol>
  );
}
