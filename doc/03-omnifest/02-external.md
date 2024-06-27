# External

External directives are directives that are implemented externally from `otk`.
They are meant to be used to provide target-specific behavior and can be used
to express things where `otk` is not expressive enough.

## Protocol

Directives are small executables that receive JSON and are expected to output
JSON again in a specific format. Additional keys are not allowed.

When we have an [omnifest](./index.md) that looks like this:

```yaml
otk.external.name:
  child:
    - 1
  options: "are here"
```

The external gets called with the following JSON:

```json
{
  "tree": {
    "otk.external.name": {
      "child": [1],
      "options": "are here"
    }
  }
}
```

And is expected to return a JSON dict with a single top-level `tree` object that can contain arbitrary values. Additional top-level keys are not allowed. Example:

```json
{
  "tree": {
    "what": {
      "you": "want"
    }
  }
}
```

Which will replace the previous `otk.external.name` subtree with the output of new subtree from the external command. Example:

```yaml
tree:
  what:
    you: "want"
```

If the external returns `{}`, an empty object, `otk` will assume that there is
no tree to replace and remove the node instead. This will turn the following
YAML:

```yaml
dummy:
  otk.external.name:
    options:
```

Into this YAML structure:

```yaml
dummy:
```

## Example

The following example demonstrates how an external can be used to implement string
concatenation.

Given the following script called `concat` in `/usr/local/libexec/otk/concat`:

```bash
#!/usr/bin/env bash

output="$(jq -jr '.tree."otk.external.concat".parts[]' <<< "${1}")"
echo "{\"tree\":{\"output\":\"$output\"}}"
```

and the following directive:

```yaml
examplestring:
  otk.external.concat:
    parts:
      - list
      - of
      - strings
```

the script is called with the following data on stdin:

```json
{
  "tree": {
    "otk.external.concat": {
      "parts": [
        "list",
        "of",
        "strings"
      ]
    }
  }
}
```

which results in the following output:

```json
{
  "tree": {
    "string": "listofstrings"
  }
}
```

and the final omnifest will be:

```yaml
examplestring:
  listofstrings
```

## Paths

`otk` will look for external directives in the following paths, stopping when
it finds the first match:

- A path defined by the `OTK_EXTERNAL_PATH` environment variable.
- `/usr/local/libexec/otk/external`
- `/usr/libexec/otk/external`
- `/usr/local/lib/otk/external`
- `/usr/lib/otk/external`

The filename for an external executable is based on the external name. When the
following directive is encountered: `otk.external.<name>` then
`otk` will try to find an executable called `<name>` in the previously
mentioned search paths.

Examples:

- `otk.external.foo` -> `foo`
- `otk.external.osbuild_bar` -> `osbuild_bar`

## Implementations

`otk` currently ships together with an external implementation for `osbuild`.
These directives can be used as children under an `otk.target.osbuild` tree.

### osbuild

These directives are only allowed within a [`otk.target.osbuild.<name>`](./01-directive.md#otktargetconsumername).

#### `otk.external.osbuild_depsolve_dnf4`

Solves a list of package specifications to RPMs and specifies them in the
osbuild manifest as sources.

#### `otk.external.osbuild_depsolve_dnf5`

Expects a `map` as its value.

`osbuild` directives to write files. **If a stage exists for the type of file
you want to write: use it.** See the [best practices](../04-best-practices.md).
