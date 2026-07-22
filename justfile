PACKAGE_NAME := "firmware-lifter"
PACKAGE_DIR := "firmware_lifter"
TEST_DIR := "tests"
CURRENT_VERSION := shell("cat $1", "VERSION")

apply-style:
    hatch fmt

lint:
    hatch fmt --check
    hatch run dev:typing

test args="":
    hatch test {{args}}

build:
    python3 -m build

release part: lint test
    #!/usr/bin/env sh
    set -eu
    if [ "{{part}}" != "patch" ] && [ "{{part}}" != "minor" ] && [ "{{part}}" != "major" ]; then
        echo >&2 "'part' must be patch, minor, or major"
        false
    fi
    hatch run dev:bumpversion "{{part}}"
    echo "Hint: see CONTRIBUTING.md for further steps if everything looks good."

publish:
    just build
    twine upload dist/{{ PACKAGE_NAME }}-{{ CURRENT_VERSION }}*
