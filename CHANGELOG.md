# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0]

- Add `expand`: POSIX shell-style expansion of `$VAR` and `${VAR}` over a mapping.
- Support the `:-`, `-`, `:+`, `+`, `:?` and `?` operators and the `$$` literal.
- Add an opt-in strict mode that raises on an unset plain reference.
- Add `ExpansionError` for malformed templates and required variables.
