// ########################################################################
// #               frontend/src/components/SourceSheet.tsx                #
// ########################################################################
// #  Author:            Kevin Street                                     #
// #  Created on:        2026-10-29                                       #
// #  Last modified on:  2026-10-29                                       #
// #  Purpose:           The cited passage on its own sheet: title,       #
// #                     section, revision date, quote marked.            #
// ########################################################################
/** The cited passage on its own sheet: title, section, date, quote marked. */

import { sectionLabel } from '../labels';
import type { Citation } from '../types';
import { Highlighted } from './Highlighted';

// log.debug('Defines the source sheet')
export function SourceSheet({ citation }: { citation: Citation }) {
  // log.debug('Returns the sheet; its key replays the highlight on each change')
  return (
    <aside className="gq-sheet" aria-label={`Source ${citation.n}`}>
      <p className="gq-sheet__n">Source {citation.n}</p>
      <h2 className="gq-sheet__title">{citation.title}</h2>
      <p className="gq-sheet__where">
        {sectionLabel(citation.section)}. Revised {citation.revised}.
      </p>
      <Highlighted key={citation.n} text={citation.passage} spans={citation.spans} />
      <p className="gq-sheet__link">
        <a href={citation.url} target="_blank" rel="noreferrer noopener">
          Read the full fact sheet on dol.gov
        </a>
      </p>
    </aside>
  );
}
