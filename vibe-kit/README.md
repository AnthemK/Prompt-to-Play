# Vibe Kit

A collection of practical micro-tools built with vibe coding.

## What This Folder Is For

`vibe-kit` is a home for small tools that are:

- useful in daily work
- fast to build and iterate
- easy to understand
- independent from one another

This folder is meant to grow over time. Each tool should solve one clear problem and stay small enough to modify through natural-language collaboration with coding agents.

## How To Use This Directory

Use `vibe-kit` as a toolbox, not as one single app.

The intended workflow is:

1. Pick a small real problem worth solving.
2. Create one dedicated subfolder for that tool.
3. Keep the tool self-contained whenever possible.
4. Document how to run it inside the tool's own `README.md`.
5. Add the tool to the index in this file.

When you want to build a new tool, the recommended pattern is:

1. Create a new folder under `vibe-kit/`.
2. Give it a short descriptive name such as `text-cleaner` or `batch-renamer`.
3. Add a local `README.md`.
4. Put code, assets, and sample files inside that folder only.
5. Avoid coupling one tool to another unless shared code becomes clearly necessary.

## Suggested Structure

```text
vibe-kit/
  README.md
  text-cleaner/
    README.md
    src/
    assets/
  batch-renamer/
    README.md
    src/
    samples/
```

This is a guideline, not a strict rule. A very small tool can be simpler:

```text
vibe-kit/
  json-pretty/
    README.md
    index.html
    app.js
    styles.css
```

## Rules For New Tools

- one tool, one folder
- one folder, one clear purpose
- keep dependencies minimal
- prefer simple setup over complex architecture
- document run instructions locally
- make tools easy to regenerate, repair, or extend with prompts

## Recommended Per-Tool README

Each tool should ideally explain:

- what problem it solves
- who it is for
- how to run it
- what files matter most
- what future improvements are planned

## Tool Index

- `bead-pattern-converter` - convert a color image into a bead-art pattern with standard color codes, preview output, and bead counts

Future entries should look like:

- `text-cleaner` - clean pasted text, remove extra spaces, normalize line breaks
- `batch-renamer` - rename files using simple rules
- `prompt-scratchpad` - draft, test, and compare prompts quickly

## Good Tool Ideas

- markdown cleaner
- filename batch renamer
- json formatter and validator
- csv to json converter
- clipboard text helper
- image resizer
- local note organizer
- prompt testing sandbox

## Philosophy

This directory follows a practical vibe-coding mindset:

- build fast
- keep scope tight
- prefer usefulness over polish
- use natural language to drive iteration

The goal is not to make a large unified platform. The goal is to accumulate small tools that are genuinely handy.
