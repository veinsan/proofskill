---
name: write-design-md
description: Use when a website needs a new or revised DESIGN.md to keep colors, typography, spacing, shapes, and components consistent across pages.
---

# Writing DESIGN.md

Create one `DESIGN.md` at the project root. It gives people and AI coding tools a shared visual reference when creating pages or components. Use the schema to define values and the Markdown sections to explain when and how to apply them.

## How to Write the File

1. Get the visual direction, values, and rules from the project brief and design references. When updating an existing file, keep the schema and Markdown sections in sync whenever a decision changes.
2. Write the schema as YAML frontmatter at the start of the file, enclosed by `---`. Add `version`, `name`, and `description` as shown in the example. Fill in the following five token groups.

   | Group | Content |
   | --- | --- |
   | `colors` | Colors by role, with hexadecimal values in quotes. |
   | `typography` | Text styles by role, with the specified font family, size, weight, and line height. |
   | `rounded` | The corner radius scale. |
   | `spacing` | The spacing scale used for gaps and padding. |
   | `components` | Component properties and states such as hover. Reference existing tokens using the form `"{colors.primary}"`. |

3. Write the eight Markdown sections in the order shown below. Use `Overview` for visual direction, `Colors` and `Typography` for color and text roles, `Layout` for grid and spacing, `Elevation & Depth` for shadow rules, `Shapes` for corner radius usage, `Components` for component roles and states, and `Do's and Don'ts` for application rules.
4. Check that each reference resolves to an existing token. Keep the Markdown rules consistent with the values and behaviors in YAML. When the project needs another color, extend the schema's palette first, then use the new token.

## Example DESIGN.md

Adapt these values to the project's design decisions.

~~~markdown
---
version: alpha
name: Portfolio Satria
description: A clean, professional, and consistent portfolio website.
colors:
  primary: "#2563EB"
  secondary: "#1E293B"
  neutral: "#F8FAFC"
  on-primary: "#FFFFFF"
typography:
  h1:
    fontFamily: Public Sans
    fontSize: 2.5rem
    fontWeight: 700
    lineHeight: 1.2
  body:
    fontFamily: Public Sans
    fontSize: 1rem
    lineHeight: 1.6
rounded:
  sm: 4px
  md: 8px
spacing:
  sm: 8px
  md: 16px
  lg: 24px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.md}"
    padding: 12px
  button-primary-hover:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.on-primary}"
  card:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.secondary}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
---

## Overview

A clean, professional personal portfolio. Use blue as the interactive accent, dark text for content, and a light background to give the page an open feel.

## Colors

- `{colors.primary}` for primary buttons, links, and interactive elements.
- `{colors.secondary}` for main text and the primary button's hover background.
- `{colors.neutral}` for page backgrounds and card surfaces.
- `{colors.on-primary}` for primary button text, including on hover.

## Typography

Use Public Sans throughout. Apply the `h1` style to bold headings and `body` to regular-weight text. Establish hierarchy with size and weight within the same font family.

## Layout

Use a 12-column grid. Use `{spacing.lg}` for gaps between sections and page padding.

## Elevation & Depth

Use flat surfaces for ordinary elements. Reserve subtle shadows for modals and dropdowns.

## Shapes

Use `{rounded.sm}` for small elements and `{rounded.md}` for cards. Use rounded corners consistently within a page.

## Components

- `button-primary` is the only primary button on each page.
- `button-primary-hover` changes the primary button's background to `{colors.secondary}` and preserves its text color.
- `card` is the default surface for grouped content.

## Do's and Don'ts

- **Do** — Use token references such as `{colors.primary}` so each value has one source.
- **Don't** — Avoid colors outside the palette. Add a palette token first when the project needs another color.
~~~
