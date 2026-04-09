# prompt-to-play

A collection of AI-generated mini-games built primarily through natural-language instructions, with little to no manual coding.

## Overview

`prompt-to-play` is a personal repository of small games created through natural-language instructions to coding agents such as Codex. The core idea is simple:

- I describe what I want in plain language
- The AI designs and implements the game
- I minimize direct code-level development as much as possible

This repository is both a playground and a record of an experiment in **natural-language-driven software creation**.

## Philosophy

The guiding principle of this repository is:

> **Use natural language as the primary development interface.**

That means:

- Game ideas are specified in prompts
- Architecture decisions are requested in prompts
- Refactors, fixes, balancing, and content extensions are also driven by prompts
- Manual coding is minimized whenever possible

The goal is not just to build games, but to explore how far AI-assisted development can go when the human mainly acts as:
- designer
- reviewer
- curator
- prompter

## What lives in this repository

This repo is intended to contain multiple small or medium-sized AI-generated game projects, for example:

- browser mini-games
- text adventures
- interactive fiction
- lightweight RPG prototypes
- turn-based demos
- experimental narrative systems

Some projects may be highly polished prototypes, while others may be rough experiments.

## Project structure

Each game should live in its own subdirectory with its own local documentation when needed.

Cross-project agent collaboration notes should live in:

- `Skills/` (shared playbooks, stage updates, and reusable practices)

Typical contents may include:

- source code
- assets
- prompts used to generate or revise the game
- project-specific README files
- AI memory / working notes
- screenshots or demo notes
- shared multi-agent skill notes under `Skills/`

The top-level repository serves as the umbrella archive for all such projects.

## Development workflow

The intended workflow is:

1. Define the game idea in natural language
2. Ask an AI coding agent to implement it
3. Ask the agent to revise, debug, refactor, or expand it
4. Review the result as a human
5. Commit the generated output
6. Repeat

In other words, this repository treats prompts as a first-class development tool.

## Goals

This repository exists to explore several questions:

- How much of game development can be done through prompting alone?
- What kinds of games are easiest for AI to build well?
- How maintainable are AI-generated codebases over time?
- Can a reusable workflow be formed around prompt-driven development?
- How far can “minimal manual coding” realistically go?

## Non-goals

This repository is **not** primarily intended to showcase hand-written engineering craftsmanship.

It is also **not** a promise that every project here is production-ready.

The emphasis is on:
- experimentation
- iteration
- playability
- documenting an AI-first creative workflow

## Notes on generated code

Because many projects in this repository are AI-generated:

- code quality may vary across projects
- architecture choices may differ from game to game
- some projects may be prototypes rather than finished products
- some projects may later be rewritten, reorganized, or replaced

Where possible, each project should document:
- how it was generated
- what tools were used
- what assumptions or constraints guided the implementation

## Licensing

See the repository `LICENSE` file for the licensing terms of this repository.

If individual subprojects require different licensing or special notices, they should include their own local documentation.

## Disclaimer

This repository may include projects inspired by existing genres, settings, or narrative traditions. Any protected third-party IP, trademarks, copyrighted text, or proprietary assets should be handled carefully and should not be included without permission.

## Status

This is an evolving repository. More projects, prompts, and documentation will be added over time.
