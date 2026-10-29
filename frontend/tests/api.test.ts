// ########################################################################
// #                      frontend/tests/api.test.ts                      #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * Tests the API client: the request it sends, and the errors it turns a
 * failed call into.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Third-party
import { afterEach, describe, expect, it, vi } from 'vitest';

// Local
import { ApiError, api, describeError } from '../src/api';
import { required } from '../src/lib/required';

// ########################################################################
// #                           API client tests                           #
// ########################################################################
// log.debug('Defines a fake fetch that answers once with the given response')
/**
 * Replaces fetch with a fake that answers with the given response.
 *
 * @param status - The response's status. Required.
 * @param body - The response's body, sent as JSON.
 * @param headers - The response's headers.
 */
function answer(
  status: number | null = null,
  body: unknown = null,
  headers: Record<string, string> = {},
): void {
  // log.debug('Takes the status, which the caller must give')
  status = required({ status });
  // log.debug('Replaces fetch for this test')
  vi.stubGlobal(
    'fetch',
    vi.fn(() => Promise.resolve(new Response(JSON.stringify(body), { status, headers }))),
  );
}

// log.debug('Describes the client')
describe('api', () => {
  // log.debug('Restores fetch after each test')
  afterEach(() => {
    // log.debug('Removes the fake')
    vi.unstubAllGlobals();
  });

  // log.debug('Checks a question is posted as JSON to the versioned route')
  it('posts a question as JSON', async () => {
    // log.debug('Answers with an empty answer')
    answer(200, { outcome: 'no_passages' });
    // log.debug('Asks the question')
    await api.ask('Is leave paid?');
    // log.debug('Reads the call fetch received')
    const [url, init] = vi.mocked(fetch).mock.calls[0] ?? [];
    // log.debug('Checks the address, method and body')
    expect([url, init?.method, init?.body]).toEqual([
      '/api/v1/ask',
      'POST',
      JSON.stringify({ question: 'Is leave paid?' }),
    ]);
  });

  // log.debug('Checks a refusal becomes an error with its reason and request id')
  it('turns a refusal into an ApiError with the server reason', async () => {
    // log.debug('Answers 429 with a reason and a request id')
    answer(429, { detail: 'too many questions; wait a minute' }, { 'X-Request-ID': 'abc' });
    // log.debug('Checks the error and how it is shown')
    await expect(api.ask('x')).rejects.toSatisfy(
      (error: unknown) =>
        error instanceof ApiError &&
        describeError(error) === 'too many questions; wait a minute (request abc)',
    );
  });

  // log.debug('Checks validation messages are joined')
  it('joins validation messages from a 422', async () => {
    // log.debug('Answers 422 with two messages')
    answer(422, { detail: [{ msg: 'too short' }, { msg: 'bad id' }] });
    // log.debug('Checks the message')
    await expect(api.sources()).rejects.toThrow('too short; bad id');
  });

  // log.debug('Checks a network failure gets a plain explanation')
  it('explains a service that did not answer', () => {
    // log.debug('Checks the explanation')
    expect(describeError(new TypeError('Failed to fetch'))).toMatch(/make run/);
  });
});
