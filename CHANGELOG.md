# webthing Changelog

## [0.11.2] - 2019-03-11
### Added
- Support for Tornado 6.x

## [0.11.1] - 2019-01-28
### Added
- Support for Python 2.7 and 3.4

## [0.11.0] - 2019-01-16
### Changed
- WebThingServer constructor can now take a list of additional API routes.
### Fixed
- Properties could not include a custom `links` array at initialization.

## [0.10.0] - 2018-11-30
### Changed
- Property, Action, and Event description now use `links` rather than `href`. - [Spec PR](https://github.com/mozilla-iot/wot/pull/119)

[Unreleased]: https://github.com/mozilla-iot/webthing-python/compare/v0.11.2...HEAD
[0.11.1]: https://github.com/mozilla-iot/webthing-python/compare/v0.11.1...v0.11.2
[0.11.1]: https://github.com/mozilla-iot/webthing-python/compare/v0.11.0...v0.11.1
[0.11.0]: https://github.com/mozilla-iot/webthing-python/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/mozilla-iot/webthing-python/compare/v0.9.2...v0.10.0
