# Changelog

All notable changes to this project will be documented in this file.

## [1.1.2] - 2021-04-09

### Added

- Option to use linked rigs (makes override and then local, keeping original linked rig for backup)
- Method of updating onion skinning while doing pose work
- In Front mode make posing and viewing onion skinning more clear
- Shortcuts for Draw, Update, Clear > allows for easy and faster workflow
- Panel shows feedback for no selection and shows if wrong object is selected (also for shortcuts)
- Links to Github issues / documentation for easier acces
- Templates to github, you get cleaner and more understandable issues that way

### Changed

- Panel layout conform 2.8 GUI
- Cleaner look enable toggles past / future
- Onion skinning most of times does not show in / opening new documents, prevents Blender restart (wip)

## [1.1.1] - 2021-04-09

### Changed

- No changes to functionality, just code cleanup.

## [1.1.0] - 2021-04-09

### Added

- New Onion Skinning mode, Inbetweening, lets you see frames with direct keyframes in a different color than interpolated frames. 

### Changed

- General cleanup to certain aspects of the code, more consistency and less try-except statements.

## [1.0.4] - 2021-04-09

### Changed

- Stop Drawing is now no longer linked to the escape key

## [1.0.3] - 2021-04-09

### Fixed

- Update bug that would switch objects instead of updating them. Turning off overlays now automatically turns off onion skins

## [1.0.2] - 2021-04-09

### Fixed

- Issues with builds not working on 2.8-2.9 versions and alpha versions

## [1.0.1] - 2017-08-11

### Added

- Build for Blender versions 2.8x

## [1.0.0] - 2017-05-30

- Initial release

## Notes

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

[0.2.3]:https://github.com/iBrushC/animationextras/releases/tag/v.0.2.3
[0.2]:https://github.com/iBrushC/animationextras/releases/tag/v0.2
[0.1]:https://github.com/iBrushC/animationextras/releases/tag/v0.1
