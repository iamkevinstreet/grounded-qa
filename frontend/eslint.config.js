// ########################################################################
// #                      frontend/eslint.config.js                       #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * Lint rules: ESLint recommended, typescript-eslint strict with types,
 * React hooks, TSDoc blocks on every named function, explicit return
 * types, and our rule that every parameter has a default.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Third-party
import js from '@eslint/js';
import { defineConfig } from 'eslint/config';
import jsdoc from 'eslint-plugin-jsdoc';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import globals from 'globals';
import tseslint from 'typescript-eslint';

// Local
import kds from './kds-eslint.js';

// ########################################################################
// #                              Lint rules                              #
// ########################################################################
// log.debug('Exports the lint rules: recommended, strict TypeScript, React hooks, doc blocks')
export default defineConfig(
  { ignores: ['dist', 'coverage'] },
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      ...tseslint.configs.strictTypeChecked,
      jsdoc.configs['flat/recommended-typescript-error'],
    ],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    plugins: { 'react-hooks': reactHooks, 'react-refresh': reactRefresh, kds },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['error', { allowConstantExport: true }],
      '@typescript-eslint/restrict-template-expressions': ['error', { allowNumber: true }],
      '@typescript-eslint/no-confusing-void-expression': ['error', { ignoreArrowShorthand: true }],
      'jsdoc/require-jsdoc': [
        'error',
        {
          contexts: [
            'FunctionDeclaration',
            'MethodDefinition',
            'VariableDeclarator > ArrowFunctionExpression',
            'VariableDeclarator > FunctionExpression',
          ],
        },
      ],
      'jsdoc/require-description': 'error',
      // One blank line between a doc block's description and its first tag, as the standard writes it.
      'jsdoc/tag-lines': ['error', 'never', { startLines: 1 }],
      'kds/param-defaults': 'error',
      // A function fits on one screen: at most 60 lines below its doc block, every line counted.
      'max-lines-per-function': ['error', { max: 60, skipBlankLines: false, skipComments: false }],
      '@typescript-eslint/explicit-function-return-type': [
        'error',
        {
          allowExpressions: true,
          allowTypedFunctionExpressions: true,
          allowHigherOrderFunctions: true,
        },
      ],
    },
  },
  {
    files: ['**/*.js'],
    extends: [js.configs.recommended],
    languageOptions: { globals: globals.node },
  },
);
