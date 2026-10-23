"""Validate generated report files against their declared $schema URIs.

Optional tool, not part of the offline unittest suite: it requires the
third-party packages ``jsonschema`` and ``referencing`` (imported lazily,
never auto-installed) and network access limited to the canonical
Microsoft JSON schema host / raw.githubusercontent.com mirror.
"""

import argparse
import json
import sys
import urllib.request
from pathlib import Path


HERE = Path(__file__).resolve().parent
PREFIX = "https://developer.microsoft.com/json-schemas/"
RAW = "https://raw.githubusercontent.com/microsoft/json-schemas/main/"
SUFFIXES = {".json", ".pbip", ".pbir", ".pbism"}
TIMEOUT = 30


def schema_url(uri):
    """Map a canonical developer schema URI to its raw GitHub document."""
    if not uri.startswith(PREFIX):
        raise ValueError(f"unexpected $schema host: {uri}")
    # Older official documents are published under the misspelled name.
    return (RAW + uri[len(PREFIX):]).replace(
        "/schema.embedded.json", "/schema-embedded.json")


def collect_instances(root):
    """Scan root for schema-bearing files.

    Returns (instances, problems): instances are (path, canonical_uri, doc)
    triples ready to validate; problems are (path, message) pairs for files
    that are malformed or declare a $schema outside the allowed host.
    """
    instances = []
    problems = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUFFIXES:
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append((path, f"invalid JSON: {exc}"))
            continue
        if not isinstance(doc, dict):
            continue
        uri = doc.get("$schema")
        if uri is None:
            continue  # e.g. the theme file declares no $schema
        if not isinstance(uri, str) or not uri.startswith(PREFIX):
            problems.append((path, f"unsupported $schema: {uri!r}"))
            continue
        instances.append((path, uri, doc))
    return instances, problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-root", type=Path, default=HERE)
    args = parser.parse_args(argv)

    if not args.report_root.is_dir():
        sys.exit(f"report root not found: {args.report_root}")

    instances, problems = collect_instances(args.report_root)
    failures = len(problems)
    for path, message in problems:
        print(f"{path}: {message}")

    try:
        import jsonschema
        import referencing
        from referencing.jsonschema import DRAFT7
    except ImportError as exc:
        sys.exit(
            f"missing optional dependency '{exc.name}': install "
            "'jsonschema' and 'referencing' yourself; this script "
            "never auto-installs"
        )

    cache = {}

    def fetch_json(uri):
        """Fetch by canonical URI; schema_url() host-checks every fetch,
        including nested $ref resolution inside the registry."""
        if uri not in cache:
            with urllib.request.urlopen(
                    schema_url(uri), timeout=TIMEOUT) as response:
                cache[uri] = json.loads(response.read().decode("utf-8"))
        return cache[uri]

    registry = referencing.Registry(
        retrieve=lambda uri: referencing.Resource.from_contents(
            fetch_json(uri), default_specification=DRAFT7))

    for path, uri, doc in instances:
        try:
            resource = registry.get_or_retrieve(uri).value
            validator = jsonschema.Draft7Validator(
                resource.contents, registry=registry)
            for error in validator.iter_errors(doc):
                failures += 1
                location = ".".join(
                    str(p) for p in error.absolute_path) or "<root>"
                print(f"{path}: {location}: {error.message}")
        except Exception as exc:  # nested resolution failures counted too
            print(f"{path}: cannot resolve {uri}: {exc}")
            failures += 1

    print(f"{len(instances)} files checked against {len(cache)} distinct "
          f"schema documents fetched; {failures} problem(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
