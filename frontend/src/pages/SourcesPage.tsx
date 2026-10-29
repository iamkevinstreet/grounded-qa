// ########################################################################
// #                  frontend/src/pages/SourcesPage.tsx                  #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The sources page: every approved fact sheet with its provenance, and
 * a reader for each.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Third-party
import { useRef, useState } from 'react';

// Local
import { api, describeError } from '../api';
import { SourceText } from '../components/SourceText';
import { CONFIG } from '../config';
import { required } from '../lib/required';
import type { SourceDetail, SourceSummary } from '../types';

// ########################################################################
// #                           Global constants                           #
// ########################################################################
// log.debug('Takes how many characters of a hash are shown from the config')
const HASH_CHARS = CONFIG.web.hash_chars;

// ########################################################################
// #                             Sources page                             #
// ########################################################################
// log.debug('Defines the sources page')
/**
 * Renders the sources page: every approved fact sheet, and a reader.
 *
 * @param props - The component's props.
 * @param props.sources - The approved sources. Required.
 * @returns The page.
 */
export function SourcesPage({
  sources = null,
}: { sources?: SourceSummary[] | null } = {}): React.JSX.Element {
  // log.debug('Takes the sources, which the caller must give')
  sources = required({ sources });
  // log.debug('Keeps the document being read')
  const [doc, setDoc] = useState<SourceDetail | null>(null);
  // log.debug('Keeps a problem loading it')
  const [problem, setProblem] = useState<string | null>(null);
  // log.debug('Remembers the latest id asked for, so a slow reply cannot win')
  const latest = useRef<string | null>(null);

  // log.debug('Defines what opening a source does')
  /**
   * Loads a source into the reader, unless a newer one was asked for.
   *
   * @param id - The id of the source to read. Required.
   */
  async function open(id: string | null = null): Promise<void> {
    // log.debug('Takes the id, which the caller must give')
    id = required({ id });
    // log.debug('Notes this as the latest request')
    latest.current = id;
    // log.debug('Clears the previous problem')
    setProblem(null);
    // log.debug('Loads the document, which may fail')
    try {
      // log.debug('Waits for the document')
      const loaded = await api.source(id);
      // log.debug('Shows it only if no newer request was made')
      if (latest.current === id) {
        // log.debug('Shows the document')
        setDoc(loaded);
      }
    } catch (error) {
      // log.debug('Shows what went wrong')
      setProblem(describeError(error));
    }
  }

  // log.debug('Returns the page')
  return (
    <div className="gq-page">
      <h1 className="gq-intro__title">Approved sources</h1>
      <p className="gq-intro__lede">
        {sources.length} public-domain fact sheets from the U.S. Department of Labor. Each one
        carries the SHA-256 of its text, and the service refuses any source whose text no longer
        matches it.
      </p>
      <div className="gq-library">
        <table className="gq-table">
          <caption className="gq-visually-hidden">Approved sources</caption>
          <thead>
            <tr>
              <th scope="col">Fact sheet</th>
              <th scope="col">Revised</th>
              <th scope="col" className="gq-table__num">
                Words
              </th>
            </tr>
          </thead>
          <tbody>
            {sources.map((source) => (
              <tr key={source.id} aria-current={doc?.id === source.id ? 'true' : undefined}>
                <td>
                  <button className="gq-link" type="button" onClick={() => void open(source.id)}>
                    {source.title}
                  </button>
                  {source.held_back && <span className="gq-flag">Held back from answers</span>}
                </td>
                <td>{source.revised}</td>
                <td className="gq-table__num">{source.words.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
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
      </div>
    </div>
  );
}
