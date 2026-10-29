// ########################################################################
// #                       frontend/vite.config.ts                        #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * Build, dev-server and test settings: React, the API proxy to port
 * 8000, and jsdom for tests. It reads config/config.toml, the settings
 * file the backend reads too, and writes only the keys the browser needs
 * into the app as __CONFIG__; nothing from config/.env reaches the app.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Standard library
import { readFileSync } from 'node:fs';

// Third-party
import react from '@vitejs/plugin-react';
import { parse } from 'smol-toml';
import { defineConfig } from 'vitest/config';

// Local
import { required } from './src/lib/required.ts';

// ########################################################################
// #                           Local constants                            #
// ########################################################################
// log.debug('Sets where the settings file is, from this folder')
const CONFIG_FILE = new URL('../config/config.toml', import.meta.url);
// log.debug('Lists the keys of each table the browser needs, and only those')
const BROWSER_KEYS: Readonly<Record<string, readonly string[]>> = {
  api: ['prefix', 'request_id_header', 'min_question_chars', 'max_question_chars'],
  llm: ['offline_provider'],
  retrieval: ['section_separator'],
  time: ['ms_per_second'],
  web: ['hash_chars'],
};

// ########################################################################
// #                            Build settings                            #
// ########################################################################
type Tables = Readonly<Record<string, Readonly<Record<string, unknown>> | undefined>>;

// log.debug('Defines how the settings the browser needs are taken from the file')
/**
 * Returns the tables and keys the browser needs from the settings file.
 *
 * @param text - The text of config/config.toml. Required.
 * @returns Each table the browser needs, holding only the keys it needs.
 */
function browserConfig(text: string | null = null): Record<string, Record<string, unknown>> {
  // log.debug('Takes the text, which the caller must give')
  text = required({ text });
  // log.debug('Parses the file into its tables')
  const tables = parse(text) as Tables;
  // log.debug('Returns each table the browser needs with only its keys')
  return Object.fromEntries(
    Object.entries(BROWSER_KEYS).map(([table, keys]) => [
      table,
      Object.fromEntries(keys.map((key) => [key, valueOf(tables, table, key)])),
    ]),
  );
}

// log.debug('Defines how one value is read, refusing a missing one')
/**
 * Returns one value from the parsed settings file.
 *
 * @param tables - The file's tables, as parsed. Required.
 * @param table - The table the value is in. Required.
 * @param key - The value's key in that table. Required.
 * @returns The value.
 * @throws {Error} When the file lacks the table or the key.
 */
function valueOf(
  tables: Tables | null = null,
  table: string | null = null,
  key: string | null = null,
): unknown {
  // log.debug('Takes the tables, which the caller must give')
  tables = required({ tables });
  // log.debug('Takes the table name, which the caller must give')
  table = required({ table });
  // log.debug('Takes the key, which the caller must give')
  key = required({ key });
  // log.debug('Reads the value, if the table and key are there')
  const value = tables[table]?.[key];
  // log.debug('Stops the build when the file lacks a value the browser needs')
  if (value === undefined) {
    // log.debug('Throws, naming the missing table and key')
    throw new Error(`config/config.toml lacks [${table}] ${key}, which the web app needs`);
  }
  // log.debug('Returns the value')
  return value;
}

// log.debug('Exports the build, dev-server and test settings')
export default defineConfig({
  plugins: [react()],
  define: { __CONFIG__: JSON.stringify(browserConfig(readFileSync(CONFIG_FILE, 'utf8'))) },
  server: {
    port: 5173,
    strictPort: true,
    proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: false } },
  },
  build: { outDir: 'dist', emptyOutDir: true, sourcemap: false },
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/**/*.test.{ts,tsx}'],
  },
});
