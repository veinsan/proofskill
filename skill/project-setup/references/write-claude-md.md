---
name: write-claude-md
description: Use when a repository needs a new or revised CLAUDE.md so Claude Code can follow the project's stack, folder boundaries, coding conventions, and development workflow.
---

# Writing CLAUDE.md

Create one `CLAUDE.md` at the project root before coding with Claude Code. Use it as a working guide for project context, where changes belong, and which rules to follow.

## How to Write the File

Use the brief and repository contents to confirm that versions, paths, features, and commands match the project. When updating `CLAUDE.md`, preserve rules that still apply. Flag important unknowns for confirmation.

1. **Project overview** — Start with the project name, what is being built, and its main purpose.
2. **Tech Stack** — Record the language, framework, important packages, package manager, and relevant versions and roles. Use this information when choosing dependencies or implementation patterns.
3. **Design system** — If the project has a theme or design system, record its themes, configuration, types, provider, and token sources. Explain which related files need to change together.
4. **Project Structure** — Show the relevant directory tree. Explain each folder's responsibility and what kinds of files belong there. Follow the existing architecture, such as grouping by layer or feature.
5. **Code Conventions** — Write concrete project rules for types, component structure, import aliases, and existing icon or styling libraries, where relevant. Instruct Claude Code to ask before writing code when a request is ambiguous.
6. **Features** — List working pages and features as a checklist. Preserve their behavior unless the task calls for a change.
7. **Do Not** — Record prohibited actions and the approved patterns where available. Cover relevant limits such as secret handling, package manager rules, wrappers, and translation locations.
8. **Testing and Build** — State whether automated tests are available, which commands to use, or how to verify changes manually. Include the build command and success criteria if the project has a build step.
9. **Git Rules** — Specify that the user handles staging, commits, and pushes. Once code changes are complete, Claude Code summarizes the result and provides the Git commands for the user to run. Match the file list, commit message, remote, and branch to the change and repository. When writing this file, record the Git rules as guidance.

## Example CLAUDE.md

Use this portfolio example as a reference for structure and detail. Adapt the stack, structure, and policies to the project being documented.

~~~markdown
# CLAUDE.md — Personal Portfolio

A Next.js portfolio website showcasing the developer's projects, skills, and experience.

## Tech Stack

| Tool | Version or role |
| --- | --- |
| Next.js | 16.1.6 with Turbopack |
| React | 19 |
| TypeScript | Strict mode |
| Tailwind CSS | v4 |
| Framer Motion | v12 for animations |
| next-intl | v4 for English and Indonesian |
| next-auth | v4 for OAuth authentication |
| next-themes | Theme management |
| Zustand | v5 for global state persisted via localStorage |
| Supabase | SSR client via `@supabase/ssr` |
| SWR | Data fetching |
| Bun | Package manager and script runner |

## Theme System

The available themes are `light`, `dark`, `yellow`, `ramadan`, and `valentine`.

- `common/constants/theme.ts` contains the theme configuration.
- `common/types/theme.ts` contains the theme types.
- `common/stores/theme.tsx` wraps the `next-themes` provider and exposes `useThemeStore`.
- `app/globals.css` contains OKLCH color tokens and Tailwind variants defined with `@custom-variant`.

## Project Structure

```text
app/
  [locale]/
    (main)/          # Pages using the main layout
    (standalone)/    # Pages using a standalone layout
  api/               # API route handlers
  globals.css        # Global styles and theme variables
common/
  components/
    elements/        # Reusable UI components
    layouts/         # Sidebar and topbar layouts
  constants/         # Static data and configuration
  stores/            # Zustand stores
  types/             # TypeScript types
  helpers/           # Utility functions
  libs/              # Third-party library wrappers
modules/             # Feature-specific components per page
services/            # API data-fetching functions
hooks/               # Custom React hooks
messages/            # en.json and id.json translations
```

## Code Conventions

- Use TypeScript strict mode and avoid `any`.
- Write functional components with explicit prop types.
- Use the `@/` import alias mapped to the project root.
- Use icons from `react-icons`, primarily `react-icons/md`.
- Merge CSS classes with `clsx` and `tailwind-merge`.
- If an instruction is ambiguous, ask what it means before coding.

## Features

- [x] Home page with an animated introduction and a list of technologies.
- [x] Projects page with cards and detail pages.
- [x] Dashboard with real-time developer statistics.
- [x] Guestbook with real-time messages via Supabase.
- [x] English and Indonesian support, a choice of sidebar or topbar layout, and five themes.

## Do Not

- Use Bun for package management and `bun run` for scripts.
- Store interface text in `messages/en.json` and `messages/id.json`. Provide both translations when adding a page.
- Access Supabase through the wrapper in `common/libs/`. Keep `SUPABASE_SERVICE_ROLE_KEY` server-side only.
- Read the theme through `useThemeStore`. When adding a theme, update `THEME_OPTIONS`, `THEME_CYCLE_ORDER`, and the corresponding variables in `app/globals.css`.
- Use `persist` middleware for new Zustand stores and SWR for data fetching.
- Keep `.env.local` and files containing real secrets out of commits.

## Testing

Verify changes manually in a browser. This project has no automated tests yet.

## Build

```bash
bun run build
```

A successful build compiles, generates about 37 static pages, and reports zero TypeScript errors.

## Git Rules

After finishing the code changes, summarize the result and provide Git commands in the response. The user runs `git add`, `git commit`, and `git push` themselves. Claude Code must leave staging, commits, and pushes to the user, including through other tools.

Provide the commands in this order, with values that match the task.

1. `git add -- <changed-file-path>` to stage files related to the task.
2. `git diff --cached` to review the changes that will be committed.
3. `git commit -m "<commit-message>"` with a message describing the change.
4. `git push <remote> <branch>` with the known remote and branch. Mark values the user needs to fill in if they are unknown.
~~~
