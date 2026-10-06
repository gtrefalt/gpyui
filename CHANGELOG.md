# Changelog

## Unreleased

- Give macOS and Windows presets distinct native control density, field surfaces,
  focus treatments, checkbox/switch sizing and slider thumbs. Keep Kit interaction
  and editing entities intact; prefer matching installed SF/Segoe font families.
- Add customizable control surface, switch and slider color tokens. Restore all
  preset hints on live switches and preserve explicit font/radius/height overrides.
- Expose popover/sidebar semantic surfaces to Python layout styles.
- Refresh native appearance PNGs, README, theme docs and both app-building skills.

## 0.4.0 — 2026-10-06

- Add macOS-inspired and Windows/Fluent-inspired native light/dark themes, plus
  shadcn-inspired Zinc and Blue presets and custom semantic color overrides.
- Add immutable Theme descriptions with configurable radii, typography and
  shadows. Preserve the default light/dark string API and platform font defaults.
- Support callback-loop theme switching with coalesced updates. Synchronize Kit
  component palettes and Base tokens without replacing native editing controls.
- Add awaited native theme snapshots, a live appearance example, eight native
  preview PNGs, source-grounded docs and updated application-building skills.
- Verify native caret, selection and undo across theme switches, reject malformed
  themes before enqueue/start, and apply every preset in installed-wheel smoke tests.

## 0.3.0 — 2026-10-05

- Add reusable Command objects with shared enabled/checked state, bindings, queued
  execution and platform-aware window shortcuts. Keep Python callbacks on asyncio.
- Add Kit DropdownMenu, nested context menus, separators and application menus.
  macOS uses the system application menu; Windows/Linux use Kit AppMenuBar.
- Refresh open drawn menus without replacing native editing controls. Validate
  command ownership, shortcut conflicts and menu updates before enqueueing.
- Add a light-theme notes editor with real async saving, native screenshots,
  command documentation and updated app-building agent skills.
- Exercise commands in installed-wheel smoke tests on every release platform
  and pointer/keyboard/menu/editing regression tests on Linux/X11.

## 0.2.0 — 2026-10-05

- Add runtime child insertion, replacement, reordering and removal to containers
  and application roots, with coalesced structural/property batches.
- Add visibility without layout space. Moving, hiding and detaching existing
  controls preserve native identity, text, caret, selection and undo history.
- Add explicit subtree disposal to release native state, subscriptions, handlers
  and bindings. Validate tree updates atomically and ignore stale disposed events.
- Refresh open dialog/sheet content and carousel bounds after child updates.
- Document the new contracts and add native editing regression tests.
- Standardize installation on `uv add` with `pip install` alternatives and add
  Python application-building and design agent skills.

## 0.1.1 — 2026-10-03

- Refresh the package README with a native light-theme dashboard PNG, a short
  first-app example, installation instructions and documentation links.
- Add the MIT license, SPDX metadata and packaged license file; retain all
  third-party notices.
- Add package project URLs and a contributor guide, and update installation docs
  for the published wheels.
- Build release wheels only on version-tag pushes. Publish tested distributions
  to GitHub and PyPI automatically; manual upload recovery reuses existing assets.

This is a packaging and documentation release. The public UI API is unchanged.

## 0.1.0 — 2026-10-02

- First published version with 71 Python controls backed by native GPUI/GPUI Kit,
  Python state bindings, queued callbacks, asyncio and batched updates.
- Native trading and component-gallery examples, visual component documentation
  and GitHub Pages.
- Six wheels for Linux, macOS and Windows on x64 and ARM64. macOS/Windows wheels
  and the source archive are available on PyPI; Linux wheels are on GitHub Releases.
