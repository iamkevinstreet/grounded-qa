// ########################################################################
// #                        frontend/src/config.ts                        #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The web app's config module, the only one that reads the build's
 * settings: the keys the browser needs from config/config.toml, which
 * vite.config.ts writes into the app when it is built, frozen as CONFIG.
 * They are the same keys the backend reads, so the two cannot drift.
 * VITE_API_BASE may point the app at another API address; by default it
 * calls the API prefix on its own origin, which the dev server proxies.
 */

// ########################################################################
// #                           Local constants                            #
// ########################################################################
// log.debug('Takes the settings the build read from config/config.toml')
const BUILT = __CONFIG__;
// log.debug('Takes the API address: VITE_API_BASE when set, else the prefix on this origin')
const API_BASE: string = import.meta.env.VITE_API_BASE ?? BUILT.api.prefix;
// log.debug('Exports the settings, frozen so no module can change them')
export const CONFIG = Object.freeze({
  api: Object.freeze({ ...BUILT.api, base: API_BASE }),
  llm: Object.freeze(BUILT.llm),
  retrieval: Object.freeze(BUILT.retrieval),
  time: Object.freeze(BUILT.time),
  web: Object.freeze(BUILT.web),
});
