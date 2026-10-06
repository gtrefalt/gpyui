# Changelog

## Unreleased

- Expose fixed-size windows, configurable minimum dimensions, initial position/state,
  movement/minimize flags, live title/size updates, native window actions and snapshots.
  Keep editor identity/caret/undo intact and restore externally resized fixed Linux windows.
- Replace the approximate macOS preset with Kit’s unchanged macOS Classic Light/Dark
  configurations from the pinned revision; retain all source colors and Kit-parsed highlights,
  use default Kit geometry/system typography and disable shadows as upstream specifies.
- Refresh Classic native previews and add window examples, docs, source evidence and skills.

- Add native Image with file/HTTP(S)/encoded-byte/bundled-asset sources, fit modes,
  aspect ratio, rounded corners, grayscale and loading/error placeholders.
- Add queued sync/async load/error callbacks, retry, stale-result guards and
  scoped decoded-image ownership. Support animated GIF/WebP, preserving adjacent
  native editors across image updates. Video streaming is a separate future API.
- Add the light image viewer, native pixel/animation/retry/lifecycle tests,
  installed-wheel smoke, component previews, image docs and agent guidance.

## 0.5.0 — 2026-10-06

- Expose real native Kit Form/Field with label layouts, grid columns, labels,
  help text, required indicators, inline errors and summary messages.
- Add sync/async Python validators and shared async submit commands, copied raw
  values, conditional field omission, stale-result guards and retryable save errors.
  Preserve text, caret, selection and native undo on failed validation.
- Add a light settings editor, real-window editing/save/retry/cancellation tests,
  installed-wheel form smoke checks, native PNGs and form docs/agent skills.

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
