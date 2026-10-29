// ########################################################################
// #                frontend/src/components/AskResult.tsx                 #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * What the ask page shows under the question: that it is searching, what
 * went wrong, an abstention, or the checked answer with its citations,
 * how it was checked, and the cited passage on its sheet.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Local
import { required } from '../lib/required';
import type { Answer } from '../types';
import { Abstention } from './Abstention';
import { AnswerText } from './AnswerText';
import { CheckDetails } from './CheckDetails';
import { CitationList } from './CitationList';
import { SourceSheet } from './SourceSheet';

// ########################################################################
// #                              Ask result                              #
// ########################################################################
export type AskState =
  | { kind: 'idle' }
  | { kind: 'asking' }
  | { kind: 'done'; answer: Answer }
  | { kind: 'failed'; message: string };

interface Props {
  state?: AskState | null;
  titles?: ReadonlyMap<string, string> | null;
  selected?: number | null;
  onSelect?: ((n: number) => void) | null;
}

// log.debug('Defines the result under the question')
/**
 * Renders what the ask page shows for where the question is.
 *
 * @param props - The component's props.
 * @param props.state - Where the question is: idle, asking, done or
 *   failed. Required.
 * @param props.titles - Each source's title by its id, for abstentions.
 *   Required.
 * @param props.selected - The number of the citation the sheet shows.
 *   Required.
 * @param props.onSelect - Shows a citation, by its number. Required.
 * @returns The result area, announced to screen readers as it changes.
 */
export function AskResult({
  state = null,
  titles = null,
  selected = null,
  onSelect = null,
}: Props = {}): React.JSX.Element {
  // log.debug('Takes where the question is, which the caller must give')
  state = required({ state });
  // log.debug('Takes the titles, which the caller must give')
  titles = required({ titles });
  // log.debug('Takes the citation shown, which the caller must give')
  selected = required({ selected });
  // log.debug('Takes what choosing a citation does, which the caller must give')
  onSelect = required({ onSelect });
  // log.debug('Finds the citation to show on the sheet')
  const citation =
    state.kind === 'done' ? state.answer.citations.find((c) => c.n === selected) : undefined;
  // log.debug('Returns the result area')
  return (
    <div className="gq-result" aria-live="polite" aria-busy={state.kind === 'asking'}>
      {state.kind === 'asking' && <p className="gq-status">Searching the fact sheets</p>}
      {state.kind === 'failed' && (
        <p className="gq-status gq-status--error" role="alert">
          {state.message}
        </p>
      )}
      {state.kind === 'done' && state.answer.outcome !== 'answered' && (
        <Abstention answer={state.answer} titles={titles} />
      )}
      {state.kind === 'done' && state.answer.outcome === 'answered' && (
        <div className="gq-result__grid">
          <article className="gq-answer" aria-label="Answer">
            <AnswerText text={state.answer.answer} selected={selected} onSelect={onSelect} />
            <CitationList
              citations={state.answer.citations}
              selected={selected}
              onSelect={onSelect}
            />
            <CheckDetails answer={state.answer} />
          </article>
          {citation && <SourceSheet citation={citation} />}
        </div>
      )}
    </div>
  );
}
