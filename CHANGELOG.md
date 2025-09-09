# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] — 2025-09-09
### Changed
- Verified compatibility and adapted project to **Python 3.13.5**.

## [1.0.0] — 2025-08-12
### Added
- First public release of **XTimer**.
- Taskbar-style timer with two orientations (horizontal/vertical).
- System tray icon with context menu.
- Time presets support (1S, 5S, 1M, etc.).
- Appearance settings: theme (light/dark), progress bar color, font and time size.
- Notifications: sound on finish, flashing border.
- Auto-update capability from server and GitHub Releases.
- Drag & drop with automatic snapping to screen edges.
- Quick add-time menu.
- Support for “Always on Top” mode.

### Fixed
- Corrected menu positioning in vertical orientation.
- Stabilized behavior when moving the timer to screen corners.

### Changed
- Optimized resource usage (separated logic and UI of the timers).
- Improved timer text rendering with outline for different themes.
