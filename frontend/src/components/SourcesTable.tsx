// ########################################################################
// #               frontend/src/components/SourcesTable.tsx               #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The table of approved fact sheets on the sources page: each one's
 * title, as a button that opens it in the reader, whether the guard held
 * it back, its revision date and its length.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Local
import { required } from '../lib/required';
import type { SourceSummary } from '../types';

// ########################################################################
// #                            Sources table                             #
// ########################################################################
interface Props {
  sources?: SourceSummary[] | null;
  current?: string | null;
  onOpen?: ((id: string) => void) | null;
}

// log.debug('Defines the table of sources')
/**
 * Renders the table of approved sources.
 *
 * @param props - The component's props.
 * @param props.sources - The approved sources. Required.
 * @param props.current - The id of the source in the reader; null when
 *   none is open.
 * @param props.onOpen - Opens a source in the reader, by its id.
 *   Required.
 * @returns The table, the open source's row marked as current.
 */
export function SourcesTable({
  sources = null,
  current = null,
  onOpen = null,
}: Props = {}): React.JSX.Element {
  // log.debug('Takes the sources, which the caller must give')
  sources = required({ sources });
  // log.debug('Takes what opening a source does, which the caller must give')
  onOpen = required({ onOpen });
  // log.debug('Returns the table')
  return (
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
          <tr key={source.id} aria-current={current === source.id ? 'true' : undefined}>
            <td>
              <button className="gq-link" type="button" onClick={() => onOpen(source.id)}>
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
  );
}
