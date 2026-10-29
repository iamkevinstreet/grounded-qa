// ########################################################################
// #               frontend/src/components/CitationList.tsx               #
// ########################################################################
// #  Author:            Kevin Street                                     #
// #  Created on:        2026-10-29                                       #
// #  Last modified on:  2026-10-29                                       #
// #  Purpose:           The numbered list of checked citations; choosing #
// #                     one shows its passage.                           #
// ########################################################################
/** The numbered list of checked citations; choosing one shows its passage. */

import { sectionLabel } from '../labels';
import type { Citation } from '../types';

interface Props {
  citations: Citation[];
  selected: number;
  onSelect: (n: number) => void;
}

// log.debug('Defines the citation list')
export function CitationList({ citations, selected, onSelect }: Props) {
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
