"""`otk-osbuild` is the [otk](https://github.com/osbuild/otk) external to work
with [osbuild](https://github.com/osbuild/osbuild) manifests.

THIS FILE IS VERY, VERY PROOF OF CONCEPT AND NEEDS TO BE CLEANED UP"""

import sys
import json
import hashlib
import base64
import pathlib
import subprocess


def source_add(kind, data):
    """Add an osbuild source to the tree."""

    # Initialize empty sources
    if data.get(kind) is None:
        data[kind] = {"items": {}}


def source_add_inline(data, text):
    return

    source_add("org.osbuild.inline", data)

    text = text.encode("utf8")
    hashsum = hashlib.sha256(text).hexdigest()
    addr = f"sha256:{hashsum}"

    if addr not in data["context"]["sources"]["org.osbuild.inline"]["items"]:
        data["org.osbuild.inline"]["items"][addr] = {
            "encoding": "base64",
            "data": base64.b64encode(text).decode("utf8"),
        }

    return hashsum, f"sha256:{hashsum}"


def source_add_curl(data, checksum, url):
    source_add("org.osbuild.curl", data)

    if checksum not in data["org.osbuild.curl"]["items"]:
        data["org.osbuild.curl"]["items"][checksum] = {"url": url}


def depsolve_dnf4_defines():
    data = json.loads(sys.stdin.read())
    args = data["tree"]["otk.external.osbuild_depsolve_dnf4_defines"]
    srcs = {}

    source_add("org.osbuild.rpm", srcs)

    request = {
        "command": "depsolve",
        "arch": args["architecture"],
        "module_platform_id": "platform:" + args["module_platform_id"],
        "releasever": args["releasever"],
        "cachedir": "/tmp",
        "arguments": {
            "root_dir": "/tmp",
            "repos": args["repositories"],
            "transactions": [
                {
                    "package-specs": args["packages"]["include"],
                    "exclude-specs": args["packages"].get("exclude", []),
                },
            ],
        },
    }

    process = subprocess.run(
        ["/usr/libexec/osbuild-depsolve-dnf"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        input=json.dumps(request),
        encoding="utf8",
        check=False,
    )

    if process.returncode != 0:
        # TODO: fix this
        raise Exception(process.stderr)  # pylint: disable=broad-exception-raised

    results = json.loads(process.stdout)

    for package in results.get("packages", []):
        source_add_curl(srcs, package["checksum"], package["remote_location"])

    sys.stdout.write(
        json.dumps({
            "tree": {
                "sources": srcs,
            },
        })
    )

    """
    sys.stdout.write(
        json.dumps(
            {
                # "context": data["context"],
                "tree": {
                    "type": "org.osbuild.rpm",
                    "inputs": {
                        "packages": {
                            "type": "org.osbuild.files",
                            "origin": "org.osbuild.source",
                            "references": [
                                {
                                    "id": package["checksum"],
                                    "options": {"metadata": {"rpm.check_gpg": True}},
                                }
                                for package in results.get("packages", [])
                            ],
                        }
                    },
                    "options": {
                        "gpgkeys": args["gpgkeys"],
                    },
                },
            }
        )
    )
    """


def noop():
    sys.stdout.write('{"tree": {}}')
