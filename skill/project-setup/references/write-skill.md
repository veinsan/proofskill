# Writing a Project Skill

Save a prompt that the project uses repeatedly, such as a test review, security review, or refactoring prompt. Give each procedure its own descriptive folder and `SKILL.md`. Use the project's established location for skills, or `skills/<skill-name>/SKILL.md` when it has no convention.

## Structure

- Use YAML frontmatter with a short `name` and a `description` that tells the agent when to load the skill.
- Put the reusable prompt or procedure in the body. State the inputs, actions, project rules, and expected output.
- Use commands and paths from the project. Flag anything that needs confirmation before it can be used.

~~~markdown
---
name: review-tests
description: Use when reviewing the tests for a project change.
---

# Review Tests

Read the changed code and the completion criteria in ARCHITECTURE.md. Compare the tests with the behavior the task is meant to deliver. Check that they cover the important behavior and any relevant failure cases.

Run the applicable test command from the project instructions. Report the command, result, and specific gaps with file references.
~~~

Keep the skill up to date when the procedure or its inputs change.
