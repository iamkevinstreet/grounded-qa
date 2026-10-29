// ########################################################################
// #                         frontend/src/api.ts                          #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The API client: one function per route, and errors that say what
 * happened and what to do.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Local
import { CONFIG } from './config';
import { required } from './lib/required';
import type { Answer, AuditEntry, Health, NewSource, SourceDetail, SourceSummary } from './types';

// ########################################################################
// #                           Global constants                           #
// ########################################################################
// log.debug('Takes the address of the API from the config')
const API_BASE = CONFIG.api.base;
// log.debug('Takes the header that carries the request id from the config')
const REQUEST_ID = CONFIG.api.request_id_header;

// ########################################################################
// #                           Local constants                            #
// ########################################################################
// log.debug('Sets the status of a response with no body')
const NO_CONTENT = 204;

// ########################################################################
// #                              API client                              #
// ########################################################################
// log.debug('Defines the error every failed call raises')
export class ApiError extends Error {
  // log.debug('Holds the HTTP status the API answered with')
  readonly status: number;
  // log.debug('Holds the request id the API gave, if any')
  readonly requestId: string | null;

  // log.debug('Defines the constructor with the status and request id')
  /**
   * Builds the error from the API's answer.
   *
   * @param status - The HTTP status the API answered with. Required.
   * @param message - What went wrong, in words a reader can act on. Required.
   * @param requestId - The request id the API gave, or null.
   */
  constructor(
    status: number | null = null,
    message: string | null = null,
    requestId: string | null = null,
  ) {
    // log.debug('Takes the status, which the caller must give')
    status = required({ status });
    // log.debug('Takes the message, which the caller must give')
    message = required({ message });
    // log.debug('Passes the message to Error')
    super(message);
    // log.debug('Names the error for logs and tests')
    this.name = 'ApiError';
    // log.debug('Keeps the status')
    this.status = status;
    // log.debug('Keeps the request id')
    this.requestId = requestId;
  }
}

// log.debug('Defines one call to the API')
/**
 * Sends one request to the API and returns its parsed answer.
 *
 * @param path - The route, after the API's address. Required.
 * @param init - The request's method, body and headers.
 * @returns The parsed body, or undefined for an empty response.
 * @throws {ApiError} When the API answers with an error status.
 */
async function call<T>(path: string | null = null, init: RequestInit = {}): Promise<T> {
  // log.debug('Takes the path, which the caller must give')
  path = required({ path });
  // log.debug('Copies the given headers, whatever form they came in')
  const headers = new Headers(init.headers);
  // log.debug('Marks the body as JSON')
  headers.set('Content-Type', 'application/json');
  // log.debug('Sends the request')
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  // log.debug('Throws with the server explanation when the call failed')
  if (!response.ok) {
    // log.debug('Throws the error with its status and request id')
    throw new ApiError(response.status, await detail(response), response.headers.get(REQUEST_ID));
  }
  // log.debug('Returns nothing for an empty response, else the parsed body')
  return (response.status === NO_CONTENT ? undefined : await response.json()) as T;
}

// log.debug('Defines how a failed response is explained')
/**
 * Returns the server's explanation of a failed response.
 *
 * @param response - The failed response. Required.
 * @returns The server's message, its validation messages joined, or a
 *   fallback that names the status.
 */
async function detail(response: Response | null = null): Promise<string> {
  // log.debug('Takes the response, which the caller must give')
  response = required({ response });
  // log.debug('Sets the fallback explanation')
  const fallback = `The request failed with status ${response.status}.`;
  // log.debug('Reads the body, which may not be JSON')
  try {
    // log.debug('Parses the body')
    const body = (await response.json()) as { detail?: unknown };
    // log.debug('Returns a plain message as it is')
    if (typeof body.detail === 'string') {
      // log.debug('Returns it')
      return body.detail;
    }
    // log.debug('Joins a list of validation messages')
    if (Array.isArray(body.detail)) {
      // log.debug('Returns each message, joined')
      return body.detail.map((item: { msg?: string }) => item.msg ?? '').join('; ');
    }
    // log.debug('Returns the fallback for any other body')
    return fallback;
  } catch {
    // log.debug('Returns the fallback when the body is not JSON')
    return fallback;
  }
}

// log.debug('Defines the header that carries the approver token')
/**
 * Returns the header that carries the approver token.
 *
 * @param token - The approver token. Required.
 * @returns The Authorization header.
 */
function bearer(token: string | null = null): HeadersInit {
  // log.debug('Takes the token, which the caller must give')
  token = required({ token });
  // log.debug('Returns the Authorization header')
  return { Authorization: `Bearer ${token}` };
}

// log.debug('Defines one function per route')
export const api = {
  health: (): Promise<Health> => call('/health'),
  ask: (question: string): Promise<Answer> =>
    call('/ask', { method: 'POST', body: JSON.stringify({ question }) }),
  sources: (): Promise<SourceSummary[]> => call('/sources'),
  source: (id: string): Promise<SourceDetail> => call(`/sources/${encodeURIComponent(id)}`),
  addSource: (token: string, source: NewSource): Promise<SourceSummary> =>
    call('/admin/sources', {
      method: 'POST',
      body: JSON.stringify(source),
      headers: bearer(token),
    }),
  removeSource: (token: string, id: string): Promise<undefined> =>
    call(`/admin/sources/${encodeURIComponent(id)}`, { method: 'DELETE', headers: bearer(token) }),
  audit: (token: string): Promise<AuditEntry[]> =>
    call('/admin/audit', { headers: bearer(token) }),
};

// log.debug('Defines the sentence shown when a call fails')
/**
 * Returns the sentence shown when a call fails.
 *
 * @param error - What the call threw; anything but an ApiError means the
 *   service did not answer.
 * @returns The server's explanation with its request id, or how to start
 *   the backend.
 */
export function describeError(error: unknown = null): string {
  // log.debug('Explains an API error with its request id, for support')
  if (error instanceof ApiError) {
    // log.debug('Returns the server explanation and the request id')
    return error.requestId ? `${error.message} (request ${error.requestId})` : error.message;
  }
  // log.debug('Explains a network failure: the service did not answer')
  return 'The service did not answer. Check that the backend is running with make run.';
}
