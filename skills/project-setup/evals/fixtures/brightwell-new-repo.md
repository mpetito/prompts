# Repository context: brightwell (new TypeScript repository, created yesterday)

Request from the lead: "We're starting this one from scratch. Set it up for agentic
development before anyone writes features."

## Team and tools

- Three developers. Each uses Claude Code locally; Codex runs background tasks.
- GitHub hosts the repo; GitHub Actions is available. Copilot is enabled for the
  organisation.
- Each feature starts with a written design and a plan that someone reviews before code.
- It will be a Node 22 HTTP service (Fastify) with a Postgres database, deployed as a
  container.

## Tree (everything that exists)

    brightwell/
    ├── README.md          (2 lines: name and one sentence)
    ├── package.json
    ├── pnpm-lock.yaml
    ├── tsconfig.json
    └── src/
        └── index.ts       (starts Fastify, one /health route)

## package.json (whole file)

    {
      "name": "brightwell",
      "private": true,
      "type": "module",
      "packageManager": "pnpm@9.15.0",
      "scripts": {
        "dev": "tsx watch src/index.ts",
        "build": "tsc -p tsconfig.json"
      },
      "dependencies": { "fastify": "^5.4.0" },
      "devDependencies": { "typescript": "^5.8.3", "tsx": "^4.20.0", "@types/node": "^22.15.0" }
    }

## tsconfig.json (compilerOptions)

    "strict": true, "target": "ES2023", "module": "NodeNext", "moduleResolution": "NodeNext",
    "outDir": "dist", "rootDir": "src"

No lint, formatter, tests, CI, agent instruction files or docs exist yet.
