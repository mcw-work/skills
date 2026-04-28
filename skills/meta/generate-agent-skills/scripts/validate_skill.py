import os
import argparse
import re
import sys

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

# Top-level fields required by the agentskills.io spec
REQUIRED_TOP_LEVEL = {"name", "description", "license"}
# Fields required under metadata: (spec-standard location)
REQUIRED_METADATA = {"author", "version"}
# Recommended metadata sub-fields
RECOMMENDED_METADATA = {"tags"}

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_TRIGGER_RES = [
    re.compile(r"\bWHEN\s*:", re.IGNORECASE),
    re.compile(r"\btrigger\b", re.IGNORECASE),
]

def validate_skill(path):
    skill_dir = os.path.basename(os.path.normpath(path))
    skill_md_path = os.path.join(path, 'SKILL.md')
    errors = []
    warnings = []

    print(f"Validating skill: {skill_dir}...")

    # 1. CRITICAL: Identity & Naming
    if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', skill_dir):
        errors.append("Directory name violates regex (lowercase/hyphens only).")

    # 2. CRITICAL: The Entry Point
    if not os.path.exists(skill_md_path):
        errors.append("Missing SKILL.md (The mandatory entry point).")

    # 3. CRITICAL: Frontmatter validation
    if os.path.exists(skill_md_path):
        with open(skill_md_path, 'r') as f:
            content = f.read()

        frontmatter = {}
        if _YAML_AVAILABLE and content.startswith("---"):
            end = content.find("\n---", 3)
            if end != -1:
                try:
                    frontmatter = yaml.safe_load(content[3:end]) or {}
                except Exception:
                    errors.append("Invalid YAML frontmatter.")

        # name
        name_val = str(frontmatter.get("name", "")).strip() if frontmatter else ""
        if not name_val:
            m = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
            name_val = m.group(1).strip() if m else ""
        if not name_val:
            errors.append("YAML frontmatter missing 'name' field.")
        elif name_val != skill_dir:
            errors.append(f"YAML name '{name_val}' mismatches directory '{skill_dir}'.")

        # description
        desc_val = str(frontmatter.get("description", "")).strip() if frontmatter else ""
        if not desc_val:
            errors.append("YAML frontmatter missing 'description' field.")
        else:
            if not any(pat.search(desc_val) for pat in _TRIGGER_RES):
                warnings.append("'description' has no trigger phrases. Add a 'WHEN: ...' clause.")

        # license (top-level per spec)
        license_val = str(frontmatter.get("license", "")).strip() if frontmatter else ""
        if not license_val:
            errors.append("YAML frontmatter missing 'license' field.")

        # metadata: block
        metadata = frontmatter.get("metadata") if frontmatter else None
        if metadata is None:
            errors.append("YAML frontmatter missing 'metadata:' block (needs author and version).")
            metadata = {}
        elif not isinstance(metadata, dict):
            errors.append("'metadata' must be a key-value mapping.")
            metadata = {}

        # metadata.version
        version_val = str(metadata.get("version", "")).strip()
        if not version_val:
            errors.append("Missing 'metadata.version' (e.g. \"1.0.0\").")
        elif not _SEMVER_RE.match(version_val):
            errors.append(f"'metadata.version' must follow SemVer X.Y.Z. Got: '{version_val}'.")

        # metadata.author
        author_val = str(metadata.get("author", "")).strip()
        if not author_val:
            errors.append("Missing 'metadata.author'.")

        # metadata.tags (recommended)
        if not metadata.get("tags"):
            warnings.append("Missing recommended 'metadata.tags' field.")

    # 4. ADVISORY: Progressive Disclosure
    if not os.path.isdir(os.path.join(path, 'references')):
        warnings.append("No 'references/' directory found. (Acceptable for simple skills).")
    if not os.path.isdir(os.path.join(path, 'scripts')):
        warnings.append("No 'scripts/' directory found. (Acceptable for pure-prompt skills).")

    # Final Report
    if errors:
        print("\n[FAIL] Critical Violations:")
        for e in errors:
            print(f"  ❌ {e}")
        sys.exit(1)
    else:
        print("\n[PASS] Skill is valid.")
        if warnings:
            print("[INFO] Advisory Notes:")
            for w in warnings:
                print(f"  ℹ️  {w}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Validate an Agent Skill.')
    parser.add_argument('--path', required=True, help='Skill root path')
    args = parser.parse_args()
    validate_skill(args.path)