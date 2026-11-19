---
name: write-readme-md
description: Use when a repository needs a new or revised README.md that explains what the project does, shows the result, and helps readers run it.
---

# Writing README.md

Make `README.md` the front page of the project. Readers should quickly understand what the project is for, see the result when available, and know how to run it. Use the brief, repository contents, and project assets to fill in the following seven parts.

1. **Project name** — Use the project name as the main heading.
2. **Short description** — In one sentence below the title, explain what kind of application it is, who it helps, and what they can do with it.
3. **Problem solved** — Explain what users struggled with before using the project. Connect that problem to the application's purpose.
4. **Key features** — List the capabilities that are already available and matter to users. Use short bullets that describe an action or outcome.
5. **Screenshot or demo** — Include a screenshot of the main page or dashboard, a link to a live demo, or a short GIF showing an important flow. Use what is relevant and available. If none is available, state that briefly in this section.
6. **Tech stack and rationale** — Name the technologies in use and explain their role and why they were chosen. If the rationale is unknown, explain the role you can verify and flag the rationale for confirmation.
7. **Installation and setup** — Give the installation and launch steps in order, starting from the correct directory. Use code blocks for commands that match the repository. Include prerequisites, configuration, or the local URL where needed and known.

Before finishing the README, check features, assets, links, and commands against the project. Preserve information that is still accurate when updating an existing README.

## Example README.md Structure

This To-Do List example shows how to fill in the parts for which information is available. Use actual project details for the installation and demo sections.

~~~markdown
# To-Do List

A task management app that helps users organize tasks by status, priority, and deadline.

## Problem Solved

Users often miss deadlines when they record tasks in a plain list. The app helps them see priorities and remember deadlines.

## Key Features

- Add and edit tasks.
- Filter tasks by status.
- Get task deadline reminders.
- Label tasks by priority.
- Use a responsive layout on mobile devices.

## Screenshot or Demo

A screenshot or demo is not yet available.

## Tech Stack and Rationale

- **React** for a component-based interface.
- **Tailwind CSS** for fast, consistent styling.
- **Supabase** for authentication and a database without building a backend from scratch.

## Installation and Setup

1. [List the prerequisites and the directory to run commands from.]
2. [Provide installation commands and any required configuration.]
3. [Provide the launch command and the local URL if available.]
~~~
