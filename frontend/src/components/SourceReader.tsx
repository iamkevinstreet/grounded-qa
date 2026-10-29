// ########################################################################
// #               frontend/src/components/SourceReader.tsx               #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The reader on the sources page: the fact sheet opened, with its
 * provenance and its whole text, or what went wrong loading it, or a
 * prompt to choose one.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Local
import { CONFIG } from '../config';
import type { SourceDetail } from '../types';
import { SourceText } from './SourceText';

// ########################################################################
// #                           Global constants                           #
// ########################################################################
// log.debug('Takes how many characters of a hash are shown from the config')
const HASH_CHARS = CONFIG.web.hash_chars;

// ########################################################################
// #                            Source reader                             #
// ########################################################################
interface Props {
  doc?: SourceDetail | null;
  problem?: string | null;
}

// log.debug('Defines the reader')
/**
 * Renders the source opened, a problem loading it, or a prompt.
 *
 * @param props - The component's props.
 * @param props.doc - The source to show; null until one is opened.
 * @param props.problem - What went wrong loading a source; null when
 *   nothing did.
 * @returns The reader, announced to screen readers as it changes.
 */
export function SourceReader({ doc = null, problem = null }: Props = {}): React.JSX.Element {
  // log.debug('Returns the reader')
  return (
    <div className="gq-reader" aria-live="polite">
      {problem && (
        <p className="gq-status gq-status--error" role="alert">
          {problem}
        </p>
      )}
      {!doc && !problem && <p className="gq-reader__empty">Choose a fact sheet to read it.</p>}
      {doc && (
        <article aria-labelledby="doc-title">
          <h2 id="doc-title" className="gq-reader__title">
            {doc.title}
          </h2>
          <dl className="gq-reader__meta">
            <dt>Publisher</dt>
            <dd>{doc.publisher}</dd>
            <dt>Revised</dt>
            <dd>{doc.revised}</dd>
            <dt>Copied</dt>
            <dd>{doc.retrieved}</dd>
            <dt>SHA-256</dt>
            <dd>
              <code title={doc.sha256}>{doc.sha256.slice(0, HASH_CHARS)}</code>
            </dd>
          </dl>
          <p className="gq-reader__link">
            <a href={doc.source} target="_blank" rel="noreferrer noopener">
              Open the original on dol.gov
            </a>
          </p>
          <SourceText body={doc.body} />
        </article>
      )}
    </div>
  );
}
