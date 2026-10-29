// ########################################################################
// #                        frontend/src/types.ts                         #
// ########################################################################
// #  Author:            Kevin Street                                     #
// #  Created on:        2026-10-29                                       #
// #  Last modified on:  2026-10-29                                       #
// #  Purpose:           The API's request and response shapes, mirroring #
// #                     the backend's pydantic models.                   #
// ########################################################################
/** The API's shapes, mirroring the backend's pydantic models. */

export type Outcome = 'answered' | 'not_covered' | 'unverified' | 'no_passages';

export type Span = readonly [number, number];

export interface Citation {
  n: number;
  passage_id: string;
  doc_id: string;
  title: string;
  section: string;
  url: string;
  revised: string;
  quote: string;
  passage: string;
  spans: Span[];
}

export interface Retrieved {
  passage_id: string;
  doc_id: string;
  score: number;
}

export interface Answer {
  question: string;
  answer: string;
  outcome: Outcome;
  citations: Citation[];
  dropped: number;
  retrieved: Retrieved[];
  model: string | null;
  prompt_version: string;
  mode: string;
  request_id: string;
}

export interface SourceSummary {
  id: string;
  title: string;
  publisher: string;
  source: string;
  revised: string;
  retrieved: string;
  sha256: string;
  words: number;
  held_back: boolean;
  flagged: string[];
}

export interface SourceDetail extends SourceSummary {
  body: string;
}

export interface Health {
  status: 'ok';
  version: string;
  sources: number;
  held_back: number;
  passages: number;
  mode: string;
  provider: string;
  model: string;
  admin: boolean;
}

export interface AuditEntry {
  id: number;
  at: string;
  action: 'add' | 'remove';
  source_id: string;
  sha256: string;
  request_id: string;
}

export interface NewSource {
  id: string;
  title: string;
  publisher: string;
  source: string;
  revised: string;
  license: string;
  body: string;
}
