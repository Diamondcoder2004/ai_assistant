#!/usr/bin/env python3
"""
Skill dependency checker for DevKit skills.
Validates required commands, npm packages, and MCP server configuration.

Usage:
    python3 preflight.py <skill-dir> [key=value ...]

Examples:
    python3 preflight.py ./path-to-skill pr=https://github.com/org/repo/pull/42
    python3 preflight.py ./path-to-skill format=png
    python3 preflight.py ./path-to-skill format=confluence
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def _normalize_frontmatter_line(line: str) -> str:
    """Strip markdown heading markers so '## name: foo' parses as YAML-like key."""
    stripped = line.strip()
    if stripped.startswith("#"):
        stripped = re.sub(r"^#+\s*", "", stripped)
    return stripped


def parse_frontmatter(skill_dir: str) -> dict:
    """Read SKILL.md and parse YAML frontmatter into a dict."""
    skill_md = Path(skill_dir) / "SKILL.md"
    if not skill_md.exists():
        print(f"  ✗ SKILL.md not found in {skill_dir}")
        sys.exit(1)

    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}

    # Simple YAML-like parser for flat/nested keys (avoids PyYAML dependency)
    frontmatter: dict = {}
    current_key = None
    current_list: list | None = None

    for line in match.group(1).splitlines():
        stripped = _normalize_frontmatter_line(line)
        if not stripped or stripped.startswith("#"):
            continue

        # Detect indentation — indented lines belong to current_key
        is_indented = line.startswith("  ") or line.startswith("\t")

        # Nested content under a parent key
        if is_indented and current_key is not None and isinstance(frontmatter.get(current_key), dict):
            # Nested inline list: key: [a, b, c]
            nested_list = re.match(r"^(\w[\w-]*):\s*\[(.+)\]$", stripped)
            if nested_list:
                nk = nested_list.group(1)
                values = [v.strip().strip("'\"") for v in nested_list.group(2).split(",")]
                frontmatter[current_key][nk] = values
                continue

            # Nested key-value pair
            nested_kv = re.match(r"^(\w[\w-]*):\s*(.+)$", stripped)
            if nested_kv:
                nk, nv = nested_kv.group(1), nested_kv.group(2).strip().strip("'\"")
                frontmatter[current_key][nk] = nv
                continue

            # List item under current key
            list_match = re.match(r"^-\s+(.+)$", stripped)
            if list_match:
                val = list_match.group(1).strip().strip("'\"")
                if not isinstance(frontmatter[current_key], list):
                    frontmatter[current_key] = []
                frontmatter[current_key].append(val)
                continue

        # Top-level inline list: key: [a, b, c]
        inline_match = re.match(r"^(\w[\w-]*):\s*\[(.+)\]$", stripped)
        if inline_match:
            key = inline_match.group(1)
            values = [v.strip().strip("'\"") for v in inline_match.group(2).split(",")]
            frontmatter[key] = values
            current_key = None
            current_list = None
            continue

        # Top-level key with no value (start of nested block)
        key_only = re.match(r"^(\w[\w-]*):\s*$", stripped)
        if key_only:
            current_key = key_only.group(1)
            frontmatter[current_key] = {}
            current_list = None
            continue

        # Top-level key-value pair
        kv_match = re.match(r"^(\w[\w-]*):\s*(.+)$", stripped)
        if kv_match:
            key, val = kv_match.group(1), kv_match.group(2).strip().strip("'\"")
            frontmatter[key] = val
            current_key = None
            current_list = None
            continue

    return frontmatter


def find_repo_root_from_skill_dir(skill_dir: Path) -> Path | None:
    """Return repo root containing skills/<this-skill>/SKILL.md, or None."""
    skill_dir = skill_dir.resolve()
    skill_name = skill_dir.name
    for parent in skill_dir.parents:
        marker = parent / "skills" / skill_name / "SKILL.md"
        if marker.exists():
            return parent
    return None


# Matches /adk:workflow and /adk-workflow (skill slug is [a-z0-9-]+)
ADK_SKILL_INVOCATION = re.compile(
    r"/adk:([a-z0-9-]+)(?![a-z0-9-])|/adk-([a-z0-9-]+)(?![a-z0-9-])"
)


def discover_invoked_helper_slugs(skill_md_text: str) -> list[str]:
    """Collect unique helper skill directory names from invocation patterns in SKILL.md."""
    seen: set[str] = set()
    order: list[str] = []
    for m in ADK_SKILL_INVOCATION.finditer(skill_md_text):
        slug = m.group(1) or m.group(2)
        if slug and slug not in seen:
            seen.add(slug)
            order.append(slug)
    return order


def warn_missing_helper_skills(skill_dir: Path, repo_root: Path | None) -> int:
    """
    For each /adk:<name> or /adk-<name> in SKILL.md, warn if skills/<name> is missing.
    Non-fatal: does not affect exit code.
    """
    skill_md = skill_dir / "SKILL.md"
    if not repo_root or not skill_md.exists():
        return 0
    skills_root = repo_root / "skills"
    if not skills_root.is_dir():
        return 0

    text = skill_md.read_text(encoding="utf-8")
    slugs = discover_invoked_helper_slugs(text)
    warned = 0
    for slug in slugs:
        if not (skills_root / slug / "SKILL.md").exists():
            print(
                f"  ⚠ Required skill not found: {slug} "
                f"(expected invocation /adk:{slug} or /adk-{slug})."
            )
            warned += 1
    return warned


def detect_provider(url: str) -> str | None:
    """Detect MCP provider from a URL or keyword."""
    lower = url.lower()
    if "github.com" in lower or lower == "github":
        return "github"
    if "bitbucket.org" in lower or lower == "bitbucket":
        return "bitbucket"
    if "atlassian.net/wiki" in lower or "confluence" in lower:
        return "atlassian-confluence"
    if "docs.google.com" in lower or "drive.google.com" in lower or lower in ("google-doc", "google-drive", "google"):
        return "google-drive"
    return None


def detect_git_provider() -> str | None:
    """Detect provider from git remote origin URL."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return detect_provider(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def check_mcp_server(name: str) -> bool:
    """Check if an MCP server is configured in ~/.claude.json or .mcp.json."""
    for config_path in [Path.home() / ".claude.json", Path(".mcp.json")]:
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                servers = data.get("mcpServers", {})
                if name in servers:
                    return True
            except (json.JSONDecodeError, KeyError):
                continue
    return False


def check_npm_package(package: str) -> bool:
    """Check if a global npm package is installed."""
    try:
        result = subprocess.run(
            ["npm", "list", "-g", "--depth=0", package],
            capture_output=True, text=True, timeout=15
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 preflight.py <skill-dir> [key=value ...]")
        sys.exit(1)

    skill_dir = sys.argv[1]
    context = {}
    for arg in sys.argv[2:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            context[k] = v

    frontmatter = parse_frontmatter(skill_dir)
    deps = frontmatter.get("dependencies", {})
    skill_name = frontmatter.get("name", Path(skill_dir).name)

    print(f"Checking dependencies for: {skill_name}")
    if context:
        print("Context:")
        for k, v in context.items():
            print(f"  - {k}={v}")

    errors = 0
    warnings = 0

    repo_root = find_repo_root_from_skill_dir(Path(skill_dir))
    helper_warnings = warn_missing_helper_skills(Path(skill_dir), repo_root)
    warnings += helper_warnings

    # Check required commands
    commands = deps.get("commands", []) if isinstance(deps, dict) else []
    if isinstance(commands, str):
        commands = [c.strip() for c in commands.split(",")]
    for cmd in commands:
        if shutil.which(cmd):
            print(f"  ✓ {cmd}")
        else:
            print(f"  ✗ {cmd} (missing)")
            errors += 1

    # Check npm packages
    npm_packages = deps.get("npm-packages", []) if isinstance(deps, dict) else []
    if isinstance(npm_packages, str):
        npm_packages = [p.strip() for p in npm_packages.split(",")]
    for pkg in npm_packages:
        if check_npm_package(pkg):
            print(f"  ✓ npm: {pkg}")
        else:
            print(f"  ✗ npm: {pkg} (missing) — Install: npm install -g {pkg}")
            errors += 1

    # Check MCP servers
    mcp_servers = deps.get("mcp-servers", []) if isinstance(deps, dict) else []
    if isinstance(mcp_servers, str):
        mcp_servers = [s.strip() for s in mcp_servers.split(",")]

    # Detect provider from context args
    detected_provider = None
    for key in ("pr", "source", "target", "provider", "format", "publish"):
        if key in context:
            detected_provider = detect_provider(context[key])
            if detected_provider:
                break

    # Auto-detect from git if skill is PR-related
    if not detected_provider and skill_name in (
        "review", "review-doc", "audit"
    ):
        detected_provider = detect_git_provider()

    # Check declared MCP servers
    for server in mcp_servers:
        if server == "detect-from-input":
            if detected_provider:
                if check_mcp_server(detected_provider):
                    print(f"  ✓ MCP: {detected_provider} (detected)")
                else:
                    print(f"  ✗ MCP: {detected_provider} not configured — See settings/mcp-setup.md")
                    errors += 1
            else:
                print(f"  ○ No MCP provider detected from input (will check at runtime)")
                warnings += 1
        else:
            if check_mcp_server(server):
                print(f"  ✓ MCP: {server}")
            else:
                print(f"  ✗ MCP: {server} not configured — See settings/mcp-setup.md")
                errors += 1

    # Check format-specific MCP (confluence, google-doc)
    fmt = context.get("format", context.get("output", "")).lower()
    if fmt == "confluence" and not check_mcp_server("atlassian-confluence"):
        print(f"  ✗ MCP: atlassian-confluence needed for confluence output — See settings/mcp-setup.md")
        errors += 1
    elif fmt == "google-doc" and not check_mcp_server("google-drive"):
        print(f"  ✗ MCP: google-drive needed for google-doc output — See settings/mcp-setup.md")
        errors += 1

    print()
    if errors > 0:
        print(f"Dependency check failed with {errors} error(s).")
        print("Fix the missing items above before running the skill.")
        sys.exit(1)
    elif warnings > 0:
        print(f"Dependency check passed with {warnings} warning(s).")
    else:
        print("Dependency check passed.")


if __name__ == "__main__":
    main()
