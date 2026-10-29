// ########################################################################
// #               frontend/src/components/SourceSheet.tsx                #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The cited passage on its own sheet: title, section, revision date,
 * quote marked.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Local
import { sectionLabel } from '../labels';
import { required } from '../lib/required';
import type { Citation } from '../types';
import { Highlighted } from './Highlighted';

// ########################################################################
// #                             Source sheet                             #
// ########################################################################
// log.debug('Defines the source sheet')
/**
 * Renders the cited passage on its own sheet.
 *
 * @param props - The component's props.
 * @param props.citation - The citation to show. Required.
 * @returns The sheet: title, section, revision date, the passage with its
 *   quote marked, and a link to the full fact sheet.
 */
export function SourceSheet({
  citation = null,
}: { citation?: Citation | null } = {}): React.JSX.Element {
  // log.debug('Takes the citation, which the caller must give')
  citation = required({ citation });
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
