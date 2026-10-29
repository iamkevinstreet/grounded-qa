// ########################################################################
// #                frontend/src/components/TokenForm.tsx                 #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The approver's token form: a password box and an Unlock button. The
 * token stays in the page's memory, never in browser storage.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Third-party
import type { SubmitEvent } from 'react';

// Local
import { required } from '../lib/required';

// ########################################################################
// #                              Token form                              #
// ########################################################################
interface Props {
  token?: string;
  onChange?: ((token: string) => void) | null;
  onUnlock?: ((event: SubmitEvent<HTMLFormElement>) => void) | null;
}

// log.debug('Defines the token form')
/**
 * Renders the form that unlocks the approver tools with the token.
 *
 * @param props - The component's props.
 * @param props.token - The token typed so far.
 * @param props.onChange - Takes the token as it is typed. Required.
 * @param props.onUnlock - Tries the token, given the form's submit event.
 *   Required.
 * @returns The form.
 */
export function TokenForm({
  token = '',
  onChange = null,
  onUnlock = null,
}: Props = {}): React.JSX.Element {
  // log.debug('Takes what typing does, which the caller must give')
  onChange = required({ onChange });
  // log.debug('Takes what unlocking does, which the caller must give')
  onUnlock = required({ onUnlock });
  // log.debug('Returns the form')
  return (
    <form className="gq-form gq-form--inline" onSubmit={onUnlock}>
      <p className="gq-form__field">
        <label htmlFor="token">Approver token</label>
        <input
          id="token"
          type="password"
          autoComplete="off"
          required
          value={token}
          onChange={(event) => onChange(event.target.value)}
        />
      </p>
      <button className="gq-button" type="submit">
        Unlock
      </button>
    </form>
  );
}
