// ########################################################################
// #               frontend/src/components/QuestionForm.tsx               #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The question box, its Ask button, and example questions to try.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Third-party
import { useState, type SubmitEvent, type KeyboardEvent } from 'react';

// Local
import { CONFIG } from '../config';
import { required } from '../lib/required';

// ########################################################################
// #                           Global constants                           #
// ########################################################################
// log.debug('Takes the shortest question the API accepts from the config')
const MIN_QUESTION_CHARS = CONFIG.api.min_question_chars;
// log.debug('Takes the longest question the API accepts from the config')
const MAX_QUESTION_CHARS = CONFIG.api.max_question_chars;

// ########################################################################
// #                           Local constants                            #
// ########################################################################
// log.debug('Lists the example questions the ask page offers')
const EXAMPLES: readonly string[] = [
  'How many weeks of FMLA leave can I take?',
  'Can my supervisor call my doctor about my leave?',
  'Do short breaks count as hours worked?',
  'Can I take FMLA leave to care for my mother-in-law?',
];

// ########################################################################
// #                            Question form                             #
// ########################################################################
interface Props {
  busy?: boolean;
  onAsk?: ((question: string) => void) | null;
}

// log.debug('Defines the question form')
/**
 * Renders the question box, its Ask button, and example questions.
 *
 * @param props - The component's props.
 * @param props.busy - Whether a question is being answered, which
 *   disables asking.
 * @param props.onAsk - Asks a question. Required.
 * @returns The form.
 */
export function QuestionForm({ busy = false, onAsk = null }: Props = {}): React.JSX.Element {
  // log.debug('Takes what asking does, which the caller must give')
  const ask = required({ onAsk });
  // log.debug('Keeps the text typed so far')
  const [text, setText] = useState('');

  // log.debug('Defines what Ask does')
  /**
   * Asks the question typed, once it is long enough.
   *
   * @param event - The form's submit event. Required.
   */
  function submit(event: SubmitEvent<HTMLFormElement> | null = null): void {
    // log.debug('Takes the event, which the caller must give')
    event = required({ event });
    // log.debug('Stops the browser from reloading the page')
    event.preventDefault();
    // log.debug('Trims the question')
    const question = text.trim();
    // log.debug('Asks only when the question is long enough')
    if (question.length >= MIN_QUESTION_CHARS) {
      // log.debug('Hands the question to the page')
      ask(question);
    }
  }

  // log.debug('Defines Enter to ask and Shift+Enter for a new line')
  /**
   * Asks on a plain Enter; Shift+Enter starts a new line.
   *
   * @param event - The key press in the question box. Required.
   */
  function keyDown(event: KeyboardEvent<HTMLTextAreaElement> | null = null): void {
    // log.debug('Takes the event, which the caller must give')
    event = required({ event });
    // log.debug('Asks on a plain Enter')
    if (event.key === 'Enter' && !event.shiftKey) {
      // log.debug('Keeps the newline out of the question')
      event.preventDefault();
      // log.debug('Submits the form as Ask would')
      event.currentTarget.form?.requestSubmit();
    }
  }

  // log.debug('Defines what choosing an example does')
  /**
   * Shows an example in the box and asks it.
   *
   * @param example - The example question. Required.
   */
  function choose(example: string | null = null): void {
    // log.debug('Takes the example, which the caller must give')
    example = required({ example });
    // log.debug('Shows the example in the box')
    setText(example);
    // log.debug('Asks it')
    ask(example);
  }

  // log.debug('Returns the form')
  return (
    <form className="gq-ask" onSubmit={submit}>
      <label className="gq-ask__label" htmlFor="question">
        Your question
      </label>
      <div className="gq-ask__row">
        <textarea
          id="question"
          className="gq-ask__box"
          rows={2}
          maxLength={MAX_QUESTION_CHARS}
          value={text}
          placeholder="For example: how much notice do I give before FMLA leave?"
          onChange={(event) => setText(event.target.value)}
          onKeyDown={keyDown}
        />
        <button className="gq-button" type="submit" disabled={busy}>
          {busy ? 'Asking' : 'Ask'}
        </button>
      </div>
      <div className="gq-examples">
        <p className="gq-examples__label" id="examples">
          Or try one of these:
        </p>
        <ul className="gq-examples__list" aria-labelledby="examples">
          {EXAMPLES.map((example) => (
            <li key={example}>
              <button
                className="gq-chip"
                type="button"
                disabled={busy}
                onClick={() => choose(example)}
              >
                {example}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </form>
  );
}
