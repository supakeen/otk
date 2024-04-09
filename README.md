# Omnifest Toolkit

This is the "Omnifest Toolkit", also known as `otk`. A YAML transpiler to
take omnifest inputs and translate them into [osbuild](https://osbuild.org)
manifests.

We are still sketching out this potential approach to generating manifests and
thus this repository is very much a work in progress.

## Documentation

There is documentation about the [format](./doc/format.md) and the available
[directives](./doc/directives.md).

## Examples

Read the [examples](./example).

## Problem(s)

A list of current problems or things that just aren't that nice yet:

- [ ] How should we structure a distribution, the [fedora](./example/fedora)
      really isn't that pretty yet.
