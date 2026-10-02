#!/usr/bin/env python3
"""Karya rebrand pass over the Plane source tree. Idempotent: run after every upstream merge.

    python3 karya/rebrand.py            # apply
    python3 karya/rebrand.py --check    # exit 1 if anything would still change (CI / pre-build gate)

What it touches (text only — never identifiers, imports, comments or copyright notices):
  1. PHRASES   — whole sentences whose meaning changes, not just the name (claims, legal, marketing).
  2. URLS      — every plane.so destination -> a CWI / Karya destination.
  3. the word  "Plane" -> "Karya" inside string literals, JSX text and i18n values.
Upstream copyright headers ("Plane Software, Inc.") and LICENSE files stay untouched (AGPL-3.0).
Hand-made changes live in their own commits; see karya/README.md.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SALES = "mailto:aniket@cwistudio.in?subject=Karya%20subscription"
SUPPORT = "mailto:hello@cwistudio.in?subject=Karya%20support"
SITE = "https://cwistudio.in"
APP = "https://karya.cwistudio.in"
SOURCE = "https://github.com/aniket328/karya"  # AGPL §13: our modified source, offered to every network user

PHRASES = {
    "Plane | Simple, extensible, open-source project management tool.": "Karya | Every piece of work, one place.",
    "Join 10,000+ teams building with Plane": "Karya by CWI Studio",
    "Plane Publish | Make your Plane boards and roadmaps pubic with just one-click. ": "Karya Publish | Share your Karya boards with one click.",
    "Plane Publish | Make your Plane boards public with one-click": "Karya Publish | Share your Karya boards with one click",
    "Plane Publish is a customer feedback management tool built on top of plane.so": "Karya Publish shares boards and work items from Karya, by CWI Studio.",
    "Made with Plane, an AI-powered work management platform with publishing capabilities.": "Made with Karya by CWI Studio.",
    "I agree to Plane marketing communications": "I agree to receive product updates from CWI Studio",
    "That crashed Plane, pun intended.": "That crashed Karya.",
    "Work in plane happens best with your team.": "Work in Karya happens best with your team.",
    "The work item is the building block of the Plane.": "The work item is the building block of Karya.",
    "Plane - Modern project management": "Karya - work management by CWI Studio",
    "Redirect to Plane": "Open Karya",
    "Plane UI": "Karya UI",
    "Plane | Accelerate software development with peace.": "Karya | Every piece of work, one place.",
    "Plane accelerated the software development by order of magnitude for agencies and product companies.": "Karya keeps every piece of work in one place.",
    "Plane helps you plan your issues, cycles, and product modules.": "Karya keeps every piece of work in one place.",
    "Plane God Mode": "Karya Admin",
    "mailto:sales@plane.so": SALES,
    "mailto:support@plane.so": SUPPORT,
    "Admin UI for Plane": "Admin UI for Karya",
    "support@plane.so": "hello@cwistudio.in",
    "help@plane.so": "hello@cwistudio.in",
    "sales@plane.so": "aniket@cwistudio.in",
    "projectplane.so": "yourcompany.com",
}
# Never rewritten: intake@plane.so is a backend identity the server compares against.

URLS = {
    "https://app.plane.so/upgrade/pro/self-hosted?plan=year": SALES,
    "https://app.plane.so/upgrade/pro/self-hosted?plan=month": SALES,
    "https://app.plane.so/upgrade/business/self-hosted?plan=year": SALES,
    "https://app.plane.so/upgrade/business/self-hosted?plan=month": SALES,
    "https://app.plane.so/og-image.png": f"{APP}/og-image.png",
    "https://plane.so/talk-to-sales": SALES,
    "https://plane.so/contact": SALES,
    "https://plane.so/business": SALES,
    "https://plane.so/pricing": SALES,
    "https://plane.so/pro": SALES,
    "https://plane.so/one": SALES,
    "https://plane.so/legals/terms-and-conditions": SITE,
    "https://plane.so/legals/privacy-policy": SITE,
    "https://plane.so/changelog?category=self-hosted": SITE,
    "https://plane.so/changelog?category=cloud": SITE,
    "https://plane.so/changelog": SITE,
    "https://go.plane.so/p-changelog": SITE,
    "https://plane.so/pages": SITE,
    "https://sites.plane.so/": SITE,
    "https://status.plane.so/": SITE,
    "https://forum.plane.so": SUPPORT,
    "https://go.plane.so/p-docs": SITE,
    "https://docs.plane.so/core-concepts/projects/run-project#estimate": SITE,
    "https://docs.plane.so/": SITE,
    "https://developers.plane.so/self-hosting/telemetry": SITE,
    "https://app.plane.so/": f"{APP}/",
    "https://plane.so/": f"{SITE}/",
    "https://plane.so": SITE,
    # email templates (apps/api/templates)
    "https://media.docs.plane.so/logo/new-logo-white.png": f"{APP}/karya/email-logo-white.png",
    "https://media.docs.plane.so/logo/new-logo-dark.png": f"{APP}/karya/email-logo-dark.png",
    "https://x.com/planepowers": SITE,
    "https://www.linkedin.com/company/planepowers/": SITE,
    "https://plane.sh/plane/0b170a1c-0e55-47cb-9307-ea49a05672b5?board=kanban": SITE,
    "https://github.com/makeplane/plane/pulls": SOURCE,
    "https://github.com/makeplane/plane/issues": SUPPORT,
    "https://github.com/makeplane/plane": SOURCE,
    "https://github.com/makeplane": SOURCE,
}

SCAN = ["apps/web", "apps/admin", "apps/space", "apps/live/src", "packages"]
SKIP_DIRS = {"node_modules", ".storybook", "design-system", "codemods", "dist", "build", ".turbo"}
EXTS = {".ts", ".tsx", ".json", ".webmanifest"}
# "Plane" as a word: not part of an identifier (PlaneLogo, IPlaneX), not a path/URL/email fragment,
# not a member access or call (Plane.x / Plane( ) and not a JSX tag (<Plane).
WORD = re.compile(r"(?<![A-Za-z0-9_./@<-])Plane(?![A-Za-z0-9_(@]|\.[A-Za-z_])")
COMMENT = re.compile(r"^\s*(//|\*|/\*)")


def files():
    for base in SCAN:
        for p in (ROOT / base).rglob("*"):
            if p.suffix in EXTS and p.is_file() and not (SKIP_DIRS & set(p.parts)) and not p.name.endswith(".stories.tsx"):
                if p.suffix == ".json" and "/locales/" not in str(p) and "manifest" not in p.name:
                    continue
                yield p


def fix_text(s: str) -> str:
    for a, b in PHRASES.items():
        s = s.replace(a, b)
    for a, b in URLS.items():
        s = s.replace(a, b)
    return s


def fix_code_line(line: str) -> str:
    if COMMENT.match(line) or "Plane Software" in line or line.lstrip().startswith(("import ", "export * from")):
        return line
    line = fix_text(line)
    if "Plane" not in line:
        return line
    # Upstream code has no bare `Plane` identifier (checked 3 Oct 2026, v1.4.2), so a word-level swap on
    # non-comment, non-import lines only hits user-facing text: string literals, JSX text, multi-line JSX.
    return WORD.sub("Karya", line)


def fix_json(obj):
    if isinstance(obj, dict):
        return {k: fix_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [fix_json(v) for v in obj]
    if isinstance(obj, str):
        # example domains in translated placeholders ("e.g. plane.so"); intake@plane.so never appears here
        return re.sub(r"(?<![@A-Za-z.])plane\.so\b", "yourcompany.com", WORD.sub("Karya", fix_text(obj)))
    return obj


API_SKIP = ("/tests/", "webhook_task.py", "openapi.py")  # webhook X-Plane-* headers are an integration contract


def api_files():
    for p in (ROOT / "apps/api/plane").rglob("*.py"):
        if not any(k in str(p) for k in API_SKIP):
            yield p
    yield from (ROOT / "apps/api/templates").rglob("*.html")


def fix_api_line(line: str) -> str:
    if line.lstrip().startswith("#") or "Plane Software" in line or line.lstrip().startswith(("import ", "from ")):
        return line
    line = fix_text(line)
    return WORD.sub("Karya", line) if "Plane" in line else line


def main():
    check = "--check" in sys.argv
    changed = []
    for p in files():
        src = p.read_text(encoding="utf-8")
        if p.suffix in (".json", ".webmanifest"):
            try:
                data = json.loads(src)
            except json.JSONDecodeError:
                continue
            new_data = fix_json(data)
            if new_data == data:
                continue
            indent = 2 if '\n  "' in src else 4
            out = json.dumps(new_data, ensure_ascii=False, indent=indent) + ("\n" if src.endswith("\n") else "")
        else:
            out = "".join(fix_code_line(l) for l in src.splitlines(keepends=True))
        if out != src:
            changed.append(p.relative_to(ROOT))
            if not check:
                p.write_text(out, encoding="utf-8")
    for p in api_files():
        src = p.read_text(encoding="utf-8")
        out = "".join(fix_api_line(l) for l in src.splitlines(keepends=True))
        if out != src:
            changed.append(p.relative_to(ROOT))
            if not check:
                p.write_text(out, encoding="utf-8")
    print(f"{'would change' if check else 'changed'} {len(changed)} files")
    for c in changed:
        print("  ", c)
    sys.exit(1 if check and changed else 0)


if __name__ == "__main__":
    main()
