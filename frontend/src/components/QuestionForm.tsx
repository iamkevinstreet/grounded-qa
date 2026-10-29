// ########################################################################
// #               frontend/src/components/QuestionForm.tsx               #
// ########################################################################
// #  Author:            Kevin Street                                     #
// #  Created on:        2026-10-29                                       #
// #  Last modified on:  2026-10-29                                       #
// #  Purpose:           The question box, its Ask button, and example    #
// #                     questions to try.                                #
// ########################################################################
/** The question box, its Ask button, and example questions to try. */

import { useState, type SubmitEvent, type KeyboardEvent } from 'react';

import { EXAMPLES, MAX_QUESTION_CHARS, MIN_QUESTION_CHARS } from '../config';

interface Props {
  busy: boolean;
  onAsk: (question: string) => void;
}

// log.debug('Defines the question form')
export function QuestionForm({ busy, onAsk }: Props) {
  // log.debug('Keeps the text typed so far')
  const [text, setText] = useState('');

  // log.debug('Defines what Ask does')
  function submit(event: SubmitEvent<HTMLFormElement>): void {
    // log.debug('Stops the browser from reloading the page')
    event.preventDefault();
    // log.debug('Trims the question')
    const question = text.trim();
    // log.debug('Asks only when the question is long enough')
    if (question.length >= MIN_QUESTION_CHARS) {
      // log.debug('Hands the question to the page')
      onAsk(question);
    }
  }

  // log.debug('Defines Enter to ask and Shift+Enter for a new line')
  function keyDown(event: KeyboardEvent<HTMLTextAreaElement>): void {
    // log.debug('Asks on a plain Enter')
    if (event.key === 'Enter' && !event.shiftKey) {
      // log.debug('Keeps the newline out of the question')
      event.preventDefault();
      // log.debug('Submits the form as Ask would')
      event.currentTarget.form?.requestSubmit();
    }
  }

  // log.debug('Defines what choosing an example does')
  function choose(example: string): void {
    // log.debug('Shows the example in the box')
    setText(example);
    // log.debug('Asks it')
    onAsk(example);
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
