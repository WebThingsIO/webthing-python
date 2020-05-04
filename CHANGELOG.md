# webthing Changelog

## [Unreleased]

## [0.13.0] - 2020-05-04
### Changed
- Invalid POST requests to action resources now generate an error status.
- Python 3.4 support dropped

## [0.12.2] - 2020-03-27
### Added
- Support OPTIONS requests to allow for CORS.

## [0.12.1] - 2020-01-13
### Changed
- Abstracted WebSocket subscriber class to allow library to work with other web frameworks.

## [0.12.0] - 2019-07-12
### Changed
- Things now use `title` rather than `name`.
- Things now require a unique ID in the form of a URI.
### Added
- Ability to set a base URL path on server.
- Support for `id`, `base`, `security`, and `securityDefinitions` keys in thing description.

## [0.11.3] - 2019-04-10
### Changed
- Simpler dependencies with no native requirements.

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

[Unreleased]: https://github.com/mozilla-iot/webthing-python/compare/v0.13.0...HEAD
[0.13.0]: https://github.com/mozilla-iot/webthing-python/compare/v0.12.2...v0.13.0
[0.12.2]: https://github.com/mozilla-iot/webthing-python/compare/v0.12.1...v0.12.2
[0.12.1]: https://github.com/mozilla-iot/webthing-python/compare/v0.12.0...v0.12.1
[0.12.0]: https://github.com/mozilla-iot/webthing-python/compare/v0.11.3...v0.12.0
[0.11.3]: https://github.com/mozilla-iot/webthing-python/compare/v0.11.2...v0.11.3
[0.11.2]: https://github.com/mozilla-iot/webthing-python/compare/v0.11.1...v0.11.2
[0.11.1]: https://github.com/mozilla-iot/webthing-python/compare/v0.11.0...v0.11.1
[0.11.0]: https://github.com/mozilla-iot/webthing-python/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/mozilla-iot/webthing-python/compare/v0.9.2...v0.10.0
