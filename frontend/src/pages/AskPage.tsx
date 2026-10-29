// ########################################################################
// #                    frontend/src/pages/AskPage.tsx                    #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The ask page: a question in; a checked answer, its citations and the
 * cited passage out, or an abstention that says why.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Third-party
import { useState } from 'react';

// Local
import { api, describeError } from '../api';
import { AskResult, type AskState } from '../components/AskResult';
import { OfflineNotice } from '../components/OfflineNotice';
import { QuestionForm } from '../components/QuestionForm';
import { CONFIG } from '../config';
import { required } from '../lib/required';
import type { Health } from '../types';

// ########################################################################
// #                           Global constants                           #
// ########################################################################
// log.debug('Takes the provider name that means the offline stand-in from the config')
const OFFLINE_PROVIDER = CONFIG.llm.offline_provider;

// ########################################################################
// #                               Ask page                               #
// ########################################################################
interface Props {
  health?: Health | null;
  titles?: ReadonlyMap<string, string> | null;
}

// log.debug('Defines the ask page')
/**
 * Renders the ask page: the question, then the checked answer.
 *
 * @param props - The component's props.
 * @param props.health - The service's health report; null until it
 *   loads.
 * @param props.titles - Each source's title by its id, for abstentions.
 *   Required.
 * @returns The page.
 */
export function AskPage({ health = null, titles = null }: Props = {}): React.JSX.Element {
  // log.debug('Takes the titles, which the caller must give')
  titles = required({ titles });
  // log.debug('Keeps where the question is: idle, asking, done or failed')
  const [state, setState] = useState<AskState>({ kind: 'idle' });
  // log.debug('Keeps which citation the source sheet shows')
  const [selected, setSelected] = useState(1);

  // log.debug('Defines what asking a question does')
  /**
   * Asks the service a question and shows the checked answer.
   *
   * @param question - The question. Required.
   */
  async function ask(question: string | null = null): Promise<void> {
    // log.debug('Takes the question, which the caller must give')
    question = required({ question });
    // log.debug('Shows that the question is being answered')
    setState({ kind: 'asking' });
    // log.debug('Asks the service, which may fail')
    try {
      // log.debug('Waits for the checked answer')
      const answer = await api.ask(question);
      // log.debug('Shows the first source with the answer')
      setSelected(1);
      // log.debug('Shows the answer')
      setState({ kind: 'done', answer });
    } catch (error) {
      // log.debug('Shows what went wrong and how to fix it')
      setState({ kind: 'failed', message: describeError(error) });
    }
  }

  // log.debug('Returns the page')
  return (
    <div className="gq-page gq-page--ask">
      <section className="gq-intro" aria-labelledby="ask-title">
        <h1 id="ask-title" className="gq-intro__title">
          Ask about federal leave and wage law
        </h1>
        <p className="gq-intro__lede">
          Answers come only from {health?.sources ?? 'the'} U.S. Department of Labor fact sheets
          approved for this service, and every quote is checked against its source before you see
          it.
        </p>
        {health?.provider === OFFLINE_PROVIDER && <OfflineNotice />}
        <QuestionForm busy={state.kind === 'asking'} onAsk={(question) => void ask(question)} />
      </section>
      <AskResult state={state} titles={titles} selected={selected} onSelect={setSelected} />
    </div>
  );
}
