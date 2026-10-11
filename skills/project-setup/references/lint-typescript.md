# TypeScript lint, CI and commit hook

Contents: [Install](#install) · [ESLint config](#eslint-config) · [Package scripts](#package-scripts)
· [Existing violations](#existing-violations) · [Duplication](#duplication) · [CI job](#ci-job) ·
[Commit hook](#commit-hook)

Every rule is `error` and lint runs with `--max-warnings 0`. A threshold is never raised and a
rule is never set to `warn` to get a repository green; existing violations go into bulk
suppressions instead. Adjust the `files` globs to the repository's layout, nothing else.

## Install

```bash
pnpm add -D eslint @eslint/js typescript-eslint eslint-plugin-sonarjs eslint-plugin-jsdoc globals jscpd prettier husky lint-staged
```

Bulk suppressions need ESLint 9.24.0 or later.

## ESLint config

`eslint.config.mjs`:

```js
import js from '@eslint/js';
import { defineConfig, globalIgnores } from 'eslint/config';
import jsdoc from 'eslint-plugin-jsdoc';
import sonarjs from 'eslint-plugin-sonarjs';
import globals from 'globals';
import tseslint from 'typescript-eslint';

const codeFiles = ['**/*.{js,mjs,cjs,ts,mts,cts,tsx}'];
const tsFiles = ['**/*.{ts,mts,cts,tsx}'];
const testFiles = ['**/*.test.{ts,tsx}', '**/test/**/*.{ts,tsx}'];
const sourceFiles = ['src/**/*.{ts,mts,tsx}'];

export default defineConfig(
  globalIgnores(['dist/**', 'coverage/**', 'report/**']),
  {
    files: codeFiles,
    extends: [js.configs.recommended],
    languageOptions: { globals: globals.node },
  },
  {
    files: tsFiles,
    extends: [tseslint.configs.strictTypeChecked],
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    rules: {
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/consistent-type-assertions': ['error', { assertionStyle: 'never' }],
      '@typescript-eslint/consistent-type-imports': ['error', { disallowTypeAnnotations: true }],
    },
  },
  {
    files: codeFiles,
    plugins: { sonarjs },
    rules: {
      complexity: ['error', 10],
      'sonarjs/cognitive-complexity': ['error', 15],
      'max-depth': ['error', 4],
      'max-params': ['error', 4],
      'max-lines-per-function': ['error', { max: 60, skipBlankLines: true, skipComments: true }],
      'max-lines': ['error', { max: 300, skipBlankLines: true, skipComments: true }],
      'no-warning-comments': 'error',
      'sonarjs/no-identical-functions': 'error',
      'sonarjs/no-identical-conditions': 'error',
      'sonarjs/no-identical-expressions': 'error',
      'sonarjs/no-all-duplicated-branches': 'error',
      'sonarjs/no-element-overwrite': 'error',
      'sonarjs/no-gratuitous-expressions': 'error',
      'sonarjs/no-ignored-return': 'error',
      'sonarjs/no-collection-size-mischeck': 'error',
      'sonarjs/no-nested-conditional': 'error',
      'sonarjs/no-hardcoded-passwords': 'error',
      'sonarjs/slow-regex': 'error',
      'sonarjs/pseudo-random': 'error',
    },
  },
  {
    // Presence of doc comments on exports only; what a comment says is code-style's concern.
    files: sourceFiles,
    ignores: testFiles,
    plugins: { jsdoc },
    settings: { jsdoc: { mode: 'typescript' } },
    rules: {
      'jsdoc/require-jsdoc': [
        'error',
        {
          publicOnly: true,
          enableFixer: false,
          require: {
            FunctionDeclaration: true,
            ClassDeclaration: true,
            ArrowFunctionExpression: true,
            FunctionExpression: true,
            MethodDefinition: true,
          },
          contexts: ['TSInterfaceDeclaration', 'TSTypeAliasDeclaration', 'TSEnumDeclaration'],
        },
      ],
    },
  },
  {
    files: testFiles,
    rules: {
      'max-lines-per-function': 'off',
      'max-lines': ['error', { max: 800, skipBlankLines: true, skipComments: true }],
    },
  },
);
```

Architecture bans (a layer that must not import another) go in the same file as
`no-restricted-imports` patterns, or in a check script under `scripts/`, never as prose alone.

## Package scripts

```json
{
  "scripts": {
    "lint": "eslint . --max-warnings 0",
    "typecheck": "tsc --noEmit",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "check:dup": "jscpd --min-tokens 50 --threshold <N> src",
    "prepare": "husky"
  }
}
```

## Existing violations

On a repository that already breaks the thresholds, keep every rule at `error` and record what is
there today ([ESLint bulk suppressions](https://eslint.org/docs/latest/use/suppressions)):

```bash
pnpm exec eslint . --suppress-all
git add eslint-suppressions.json
```

- New violations fail; a suppressed count may only fall. When it falls, ESLint fails with
  "There are suppressions left that do not occur anymore" until you run
  `pnpm exec eslint . --prune-suppressions` and commit the smaller file.
- A file kept anywhere but the root needs `--suppressions-location <path>` on every run, CI included.
- Never `--suppress-all` again to hide a new violation; fix the code.

## Duplication

[jscpd](https://github.com/kucherenko/jscpd) reports copy-pasted blocks across files;
`sonarjs/no-identical-functions` catches identical functions within one. Run
`pnpm exec jscpd --min-tokens 50 src` once, then set `--threshold` in `check:dup` to the
percentage that first report shows, so it fails only when duplication grows. Unverified: the
exit code on a clone below the threshold; confirm on the first run.

## CI job

`.github/workflows/ci.yml`. A skipped workflow leaves a required check pending and blocks the
merge ([GitHub docs](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks#handling-skipped-but-required-checks)),
so docs-only PRs skip the job, not the workflow: a skipped job reports success.

```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
concurrency:
  group: ci-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      code: ${{ steps.diff.outputs.code }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          fetch-depth: 0
          persist-credentials: false
      - id: diff
        env:
          BASE: ${{ github.event.pull_request.base.sha }}
        run: |
          if [ -z "$BASE" ] || git diff --name-only "$BASE" HEAD | grep -qvE '\.md$|^docs/|^specs/'; then
            echo "code=true" >> "$GITHUB_OUTPUT"
          else
            echo "code=false" >> "$GITHUB_OUTPUT"
          fi
  ci:
    needs: changes
    if: needs.changes.outputs.code == 'true'
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: pnpm/action-setup@ea17c68df8912ef543352723c149a84f56e3d413 # v6.1.0
      - uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
        with:
          node-version-file: .nvmrc
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm typecheck
      - run: pnpm lint
      - run: pnpm format:check
      - run: pnpm check:dup
      - run: pnpm test
```

Make `ci` the required check in branch protection. Pin actions by commit SHA; look one up with
`gh api repos/<owner>/<action>/commits/<tag> --jq .sha`.

## Commit hook

Formatting is fixed at commit; CI is the backstop for everything else.

```bash
pnpm exec husky init
echo "pnpm exec lint-staged" > .husky/pre-commit
```

`package.json`:

```json
{
  "lint-staged": {
    "*": "prettier --write --ignore-unknown"
  }
}
```
