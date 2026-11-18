#!/usr/bin/env python3
"""Validate YAML, resolve audit vs production views, compile Typst PDFs + HTML."""
import datetime
import json
import os
import re
import subprocess
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
VIEWS_DIR = ROOT / "views"
DIST_DIR = ROOT / "dist"
SITE_DIR = ROOT / "site"

LINK_RE = re.compile(r"(\^?)\[([^\]]+)\]\(([^)]+)\)")

NBSP = "\u00A0"
MONTHS = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"


def apply_nbsp(obj):
    if isinstance(obj, dict):
        return {k: apply_nbsp(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [apply_nbsp(v) for v in obj]
    if isinstance(obj, str):
        obj = re.sub(rf"\b({MONTHS}) (\d{{1,2}}), (\d{{4}})\b", rf"\1{NBSP}\2,{NBSP}\3", obj)
        obj = re.sub(rf"\b({MONTHS}) (\d{{1,2}})\b", rf"\1{NBSP}\2", obj)
        obj = re.sub(r"\b(TU|UC|Dr\.|Prof\.|Vol\.|No\.|S\.) ", rf"\1{NBSP}", obj)
    return obj

def get_git_meta() -> tuple[str, str, str]:
    now = datetime.datetime.now()
    last_update = now.strftime("%B %d, %Y")
    iso_date = now.strftime("%Y-%m-%dT%H:%M:%S")
    commit_sha = os.environ.get("CI_COMMIT_SHORT_SHA", "")
    try:
        date_out = subprocess.check_output(
            ["git", "log", "-1", "--format=%cd", "--date=format:%B %d, %Y"],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        iso_out = subprocess.check_output(
            ["git", "log", "-1", "--format=%cd", "--date=format:%Y-%m-%dT%H:%M:%S"],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        sha_out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        if date_out:
            last_update = date_out
        if iso_out:
            iso_date = iso_out
        if sha_out:
            commit_sha = sha_out
    except Exception:
        pass
    return last_update, iso_date, commit_sha


def validate_urls(obj, path="root"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            validate_urls(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            validate_urls(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        for _, label, url in LINK_RE.findall(obj):
            if not url.startswith(("https://", "http://", "mailto:")):
                raise ValueError(f"Invalid URL scheme at {path} [{label}]: {url!r}")
            if " " in url or "https://https://" in url:
                raise ValueError(f"Malformed URL at {path} [{label}]: {url!r}")


def load_all_data() -> dict:
    data = {}
    for f in sorted(DATA_DIR.glob("*.yaml")):
        content = yaml.safe_load(f.read_text(encoding="utf-8"))
        validate_urls(content, f.stem)
        content = apply_nbsp(content)
        data[f.stem] = content
    return data


def years_from_entries(entries: list[dict]) -> tuple[int, int]:
    years = []
    for e in entries:
        raw = str(e.get("year") or e.get("period") or "")
        years.extend(int(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b", raw))
    return (min(years), max(years)) if years else (0, 0)


def filter_entries(entries: list[dict], exclude_tags: set[str]) -> list[dict]:
    return [e for e in entries if not (set(e.get("tags", [])) & exclude_tags)]


def apply_rule(entries: list[dict], rule: dict | None, exclude_tags: set[str]) -> list[dict]:
    filtered = filter_entries(entries, exclude_tags)
    if not rule:
        return filtered

    kw = rule["keep_where"]
    field, allowed = kw["field"], kw.get("in")
    kept, rest = [], []
    for e in filtered:
        val = e.get(field)
        match = (val in allowed) if allowed is not None else (val == kw.get("equals"))
        (kept if match else rest).append(e)

    agg_cfg = rule.get("aggregate_remaining")
    if agg_cfg and rest:
        min_y, max_y = years_from_entries(rest)
        insts = list(dict.fromkeys(e.get("institution", "") for e in rest if e.get("institution")))
        insts_str = ", ".join(insts) if insts else "TU Dresden"
        summary_text = agg_cfg["template"].format(
            count=len(rest), min_year=min_y, max_year=max_y, institutions_list=insts_str
        ).strip()
        kept.append({
            "period": agg_cfg["period"].format(min_year=min_y, max_year=max_y),
            "text": summary_text,
            "is_summary": True,
        })
    return kept


def resolve_view(raw: dict, view_cfg: dict, last_update: str, iso_date: str, commit_sha: str) -> dict:
    exclude = set(view_cfg.get("exclude_tags", []))
    rules = view_cfg.get("rules", {})
    if view_cfg.get("include_all"):
        exclude = set()
        rules = {}

    grants = raw["grants"]
    return {
        "meta": {
            "view": view_cfg["name"],
            "last_update": last_update,
            "iso_date": iso_date,
            "commit_sha": commit_sha,
            "closing_note": view_cfg.get("closing_note", "").strip(),
        },
        "profile": raw["profile"],
        "education": filter_entries(raw["education"], exclude),
        "appointments": raw["appointments"],
        "experience": filter_entries(raw["experience"], exclude),
        "publications": {k: filter_entries(v, exclude) for k, v in raw["publications"].items()},
        "talks": filter_entries(raw["talks"], exclude),
        "teaching": filter_entries(raw["teaching"], exclude),
        "theses": apply_rule(raw["theses"], rules.get("theses"), exclude),
        "service": {k: filter_entries(v, exclude) for k, v in raw["service"].items()},
        "grants": {
            "awarded": filter_entries(grants.get("awarded", []), exclude),
            "pending": filter_entries(grants.get("pending", []), exclude),
            "declined": filter_entries(grants.get("declined", []), exclude) if view_cfg.get("show_declined_grants", True) else [],
            "phd_projects": filter_entries(grants.get("phd_projects", []), exclude) if view_cfg.get("show_phd_project_work", True) else [],
        },
        "awards": filter_entries(raw["awards"], exclude),
        "freelance": apply_rule(raw["freelance"], rules.get("freelance"), exclude),
        "media": filter_entries(raw["media"], exclude),
        "software": filter_entries(raw["software"], exclude),
    }


def md_to_html(text: str) -> str:
    def format_inline(s: str) -> str:
        def repl_link(m):
            sup, label, url = m.groups()
            return f'<sup><a href="{url}">[{label}]</a></sup>' if sup else f'<a href="{url}">{label}</a>'

        s = LINK_RE.sub(repl_link, s)
        s = re.sub(r"\*\*\*((?:[^*\\]|\\.)+)\*\*\*", r"<strong><em>\1</em></strong>", s)
        s = re.sub(r"\*\*((?:[^*\\]|\\.)+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*((?:[^*\\]|\\.)+)\*", r"<em>\1</em>", s)
        return s.replace(r"\*", "*")

    out, in_ul = [], False
    for line in text.split("\n"):
        if line.startswith("- "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{format_inline(line[2:])}</li>")
        else:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(format_inline(line) + "<br>")
    if in_ul:
        out.append("</ul>")
    return "".join(out).removesuffix("<br>")


def main():
    DIST_DIR.mkdir(exist_ok=True)
    SITE_DIR.mkdir(exist_ok=True)
    raw = load_all_data()
    last_update, iso_date, commit_sha = get_git_meta()

    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=False)
    env.filters["rich"] = md_to_html
    html_tpl = env.get_template("cv.html.j2")

    outputs = [
        ("production", "cv_alexanderdunkel.pdf", "cv.html"),
        ("audit", "cv_alexanderdunkel_audit.pdf", "cv_audit.html"),
    ]

    for view_name, pdf_name, html_name in outputs:
        view_cfg = yaml.safe_load((VIEWS_DIR / f"{view_name}.yaml").read_text(encoding="utf-8"))
        resolved = resolve_view(raw, view_cfg, last_update, iso_date, commit_sha)

        json_path = DIST_DIR / f"resolved_{view_name}.json"
        json_path.write_text(json.dumps(resolved, indent=2, ensure_ascii=False), encoding="utf-8")

        subprocess.run(
            [
                "typst", "compile",
                "--pdf-standard", "1.7,a-2b,ua-1",
                "--root", str(ROOT),
                "--input", f"data={json_path.relative_to(ROOT)}",
                str(ROOT / "templates/cv.typ"),
                str(SITE_DIR / pdf_name),
            ],
            check=True,
        )
        (SITE_DIR / html_name).write_text(html_tpl.render(cv=resolved), encoding="utf-8")
        print(f"Built {view_name}: site/{pdf_name} & site/{html_name}")


if __name__ == "__main__":
    main()
