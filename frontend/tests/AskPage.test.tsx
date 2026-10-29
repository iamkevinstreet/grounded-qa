// ########################################################################
// #                   frontend/tests/AskPage.test.tsx                    #
// ########################################################################
// #  Author:            Kevin Street                                     #
// #  Created on:        2026-10-29                                       #
// #  Last modified on:  2026-10-29                                       #
// #  Purpose:           Tests the ask page end to end against a stubbed  #
// #                     API: answers, highlights, abstentions.           #
// ########################################################################
/** Tests the ask page end to end against a stubbed API. */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { api } from '../src/api';
import { AskPage } from '../src/pages/AskPage';
import type { Answer, Citation } from '../src/types';

// log.debug('Defines a checked citation for the stubbed answers')
function cite(n: number, passage: string, quote: string): Citation {
  // log.debug('Finds where the quote sits in its passage')
  const start = passage.indexOf(quote);
  // log.debug('Returns the citation with that range')
  return {
    n,
    passage_id: `fs28#${n}`,
    doc_id: 'dol-whd-fs28',
    title: 'Fact Sheet #28: The Family and Medical Leave Act',
    section: 'USING FMLA LEAVE',
    url: 'https://www.dol.gov/agencies/whd/fact-sheets/28-fmla',
    revised: 'March 2025',
    quote,
    passage,
    spans: [[start, start + quote.length]],
  };
}

// log.debug('Sets an answered response with two citations')
const ANSWERED: Answer = {
  question: 'How long is FMLA leave?',
  answer: 'Up to 12 workweeks [1]. The leave is unpaid [2].',
  outcome: 'answered',
  citations: [
    cite(1, 'Eligible employees may take up to 12 workweeks of leave.', 'up to 12 workweeks'),
    cite(2, 'FMLA is job-protected, unpaid leave.', 'job-protected, unpaid leave'),
  ],
  dropped: 0,
  retrieved: [{ passage_id: 'fs28#1', doc_id: 'dol-whd-fs28', score: 0.03 }],
  model: 'claude-sonnet-5-5',
  prompt_version: '2026-10-29',
  mode: 'keyword',
  request_id: 'req-1',
};

// log.debug('Describes the ask page')
describe('AskPage', () => {
  // log.debug('Checks an answer shows its first source, quote highlighted')
  it('shows the answer and highlights the quote of the chosen source', async () => {
    // log.debug('Stubs the API to answer')
    vi.spyOn(api, 'ask').mockResolvedValue(ANSWERED);
    // log.debug('Renders the page')
    render(<AskPage health={null} titles={new Map()} />);
    // log.debug('Types and asks a question')
    await userEvent.type(screen.getByLabelText('Your question'), 'How long is FMLA leave?{Enter}');
    // log.debug('Checks the first quote is highlighted')
    expect(await screen.findByText('up to 12 workweeks', { selector: 'mark' })).toBeVisible();
    // log.debug('Chooses the second source by its marker')
    await userEvent.click(screen.getByRole('button', { name: 'Show source 2' }));
    // log.debug('Checks the second quote is now highlighted')
    expect(screen.getByText('job-protected, unpaid leave', { selector: 'mark' })).toBeVisible();
  });

  // log.debug('Checks an abstention says so and names what was searched')
  it('explains an abstention and lists the fact sheets searched', async () => {
    // log.debug('Stubs the API to abstain')
    vi.spyOn(api, 'ask').mockResolvedValue({
      ...ANSWERED,
      answer: 'The passages do not mention California.',
      outcome: 'not_covered',
      citations: [],
    });
    // log.debug('Renders the page with a title for the searched sheet')
    render(<AskPage health={null} titles={new Map([['dol-whd-fs28', 'Fact Sheet #28']])} />);
    // log.debug('Asks with one of the examples')
    await userEvent.click(screen.getByRole('button', { name: /mother-in-law/ }));
    // log.debug('Checks the heading, the reason and the searched sheet')
    expect(await screen.findByRole('heading', { name: /do not cover this/ })).toBeVisible();
    // log.debug('Checks the reason from the model')
    expect(screen.getByText('The passages do not mention California.')).toBeVisible();
    // log.debug('Checks the searched sheet is named')
    expect(screen.getByText('Fact Sheet #28')).toBeVisible();
  });
});
