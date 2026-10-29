// ########################################################################
// #               frontend/src/components/QuestionBox.tsx                #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The question box and its Ask button: Enter asks, Shift+Enter starts a
 * new line, and the box takes no more than the API accepts.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Third-party
import type { KeyboardEvent } from 'react';

// Local
import { CONFIG } from '../config';
import { required } from '../lib/required';

// ########################################################################
// #                           Global constants                           #
// ########################################################################
// log.debug('Takes the longest question the API accepts from the config')
const MAX_QUESTION_CHARS = CONFIG.api.max_question_chars;

// ########################################################################
// #                             Question box                             #
// ########################################################################
interface Props {
  text?: string;
  busy?: boolean;
  onChange?: ((text: string) => void) | null;
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

// log.debug('Defines the question box')
/**
 * Renders the question box with its label and its Ask button.
 *
 * @param props - The component's props.
 * @param props.text - The text typed so far.
 * @param props.busy - Whether a question is being answered, which
 *   disables asking.
 * @param props.onChange - Takes the text as it is typed. Required.
 * @returns The label, then the row holding the box and the button.
 */
export function QuestionBox({
  text = '',
  busy = false,
  onChange = null,
}: Props = {}): React.JSX.Element {
  // log.debug('Takes what typing does, which the caller must give')
  onChange = required({ onChange });
  // log.debug('Returns the label, the box and the button')
  return (
    <>
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
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={keyDown}
        />
        <button className="gq-button" type="submit" disabled={busy}>
          {busy ? 'Asking' : 'Ask'}
        </button>
      </div>
    </>
  );
}
