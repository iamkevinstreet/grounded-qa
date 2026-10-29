// ########################################################################
// #                      frontend/src/globals.d.ts                       #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * Declares the globals every module may use without an import: the
 * trace logger, the settings the build writes in from config/config.toml
 * (read only through src/config.ts), and the one build variable the app
 * reads, VITE_API_BASE.
 */

// ########################################################################
// #                         Global declarations                          #
// ########################################################################
declare const log: { debug(message: string): void };

declare const __CONFIG__: {
  api: {
    prefix: string;
    request_id_header: string;
    min_question_chars: number;
    max_question_chars: number;
  };
  llm: { offline_provider: string };
  retrieval: { section_separator: string };
  time: { ms_per_second: number };
  web: { hash_chars: number };
};

interface ImportMetaEnv {
  readonly VITE_API_BASE?: string;
}
