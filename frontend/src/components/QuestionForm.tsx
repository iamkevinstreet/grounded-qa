// ########################################################################
// #               frontend/src/components/QuestionForm.tsx               #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The question form on the ask page: the box, its Ask button and the
 * example questions, asking a question once it is long enough.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Third-party
import { useState, type SubmitEvent } from 'react';

// Local
import { CONFIG } from '../config';
import { required } from '../lib/required';
import { ExampleQuestions } from './ExampleQuestions';
import { QuestionBox } from './QuestionBox';

// ########################################################################
// #                           Global constants                           #
// ########################################################################
// log.debug('Takes the shortest question the API accepts from the config')
const MIN_QUESTION_CHARS = CONFIG.api.min_question_chars;

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
      <QuestionBox text={text} busy={busy} onChange={setText} />
      <ExampleQuestions busy={busy} onChoose={choose} />
    </form>
  );
}
