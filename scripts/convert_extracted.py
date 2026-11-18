#!/usr/bin/env python3
"""One-time converter: extracted_idml.json -> clean, normalized data/*.yaml.

This is EOL - I used it once to migrate my InDesign CV to the Typst version.
"""
import json
import re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


class LiteralDumper(yaml.SafeDumper):
    pass


def _str_representer(dumper, data):
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


LiteralDumper.add_representer(str, _str_representer)


def clean_line(ln: str) -> str:
    ln = ln.replace("\u2028", " ")
    # Escape literal German gender-star before formatting cleanup
    ln = ln.replace("Tourist*innen", r"Tourist\*innen")
    # Fix nested ^[[label]](url) -> ^[label](url)
    ln = re.sub(r"\^\[\[([^\]]+)\]\]\(([^)]+)\)", r"^[\1](\2)", ln)
    # Protect bold+italic "***and***"
    ln = ln.replace("*****and*****", "___BOLDITALIC_AND___")
    # Collapse empty/adjacent bold runs on same line (horizontal whitespace only!)
    ln = ln.replace("****", "")
    ln = re.sub(r"\*\*[ \t]+\*\*", " ", ln)
    # Fix bold->italic boundaries
    ln = ln.replace("*****", "** *")
    ln = re.sub(r"\.[ \t]*\*\*\*[ \t]*", ".** *", ln)
    ln = re.sub(r"\*\*\*[ \t]+\*\*", "* **", ln)
    ln = re.sub(r"\*\*\*[ \t]+", "* ", ln)
    ln = re.sub(r"[ \t]+\*\*\*", " *", ln)
    # Move trailing/leading spaces outside markers
    ln = re.sub(r"\*\*([^*]+?)[ \t]+\*\*", r"**\1** ", ln)
    ln = re.sub(r"(?<!\*)\*([^*]+?)[ \t]+\*(?!\*)", r"*\1* ", ln)
    ln = ln.replace("___BOLDITALIC_AND___", "** ***and*** **")
    return re.sub(r" {2,}", " ", ln).strip()


def clean(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\u2028", "\n")
    lines = [clean_line(ln) for ln in text.split("\n")]
    return "\n".join(ln for ln in lines if ln)


def write_yaml(name: str, obj):
    (DATA_DIR / f"{name}.yaml").write_text(
        yaml.dump(obj, Dumper=LiteralDumper, allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )


def main():
    raw = json.loads((ROOT / "extracted_idml.json").read_text(encoding="utf-8"))
    u145 = raw["story_u145_tables"]
    u163 = raw["story_u163_tables"]

    # 00 Profile
    write_yaml("profile", {
        "name": "Alexander Dunkel",
        "degrees": "Dr.-Ing. habil. [PhD / Habilitation], Dipl.-Ing. [MA]",
        "role": "Senior Scientist",
        "affiliation_line1": "Transformative Capacities & Research Data Centre,",
        "affiliation_line2": "Leibniz Institute of Ecological Urban and Regional Development, Germany",
        "emails": ["a.dunkel@ioer.de", "alexander.dunkel@gmail.com"],
        "web": "alexanderdunkel.com",
        "phone": "+49 351 463-32671",
        "closing_text": (
            "A visual counterpart of this CV can be found at "
            "[alexanderdunkel.com/time](https://alexanderdunkel.com/time)\n\n"
            "I try to do transparent, open, and reproducible science, as much as possible. "
            "Most of what I do or create is shared at [links.alexanderdunkel.com/](https://links.alexanderdunkel.com/). "
            "I also occasionally toot [@alex@himself.alexanderdunkel.com](https://himself.alexanderdunkel.com/). "
            "My personal efforts at self-hosting and digital liberation are documented at [du.nkel.dev](https://du.nkel.dev).\n\n"
            "My git repositories can be found at [github.com/sieboldianus](https://github.com/sieboldianus), "
            "[gitlab.vgiscience.de/ad](https://gitlab.vgiscience.de/ad), and "
            "[gitlab.hrz.tu-chemnitz.de/s7398234--tu-dresden.de](https://gitlab.hrz.tu-chemnitz.de/s7398234--tu-dresden.de)."
        ),
    })

    # 01 Education
    edu_rows = []
    for idx, (period, body) in enumerate(u145[0]):
        if idx == 0:
            edu_rows.append({
                "id": "edu-habil",
                "period": "2024–2026",
                "institution": "Technische Universität Dresden",
                "country": "Germany",
                "details": (
                    "Habilitation (completed Oct 15, 2026), Faculty of Environmental Sciences; "
                    "*Geovisualizing Collective Perception: Integrating Opportunistic Data into the Planning Information Cycle*"
                ),
                "tags": ["core"],
            })
            continue
        lines = clean(body).split("\n")
        inst_part = lines[0].replace("**", "")
        inst, country = [x.strip() for x in inst_part.split(",", 1)]
        details = " ".join(lines[1:]) if len(lines) > 1 else ""
        edu_rows.append({
            "id": f"edu-{idx}",
            "period": period,
            "institution": inst,
            "country": country,
            "details": details,
            "tags": ["core"],
        })
    write_yaml("education", edu_rows)

    # 02 Academic Appointments
    appts = []
    for idx, tbl in enumerate(u145[1:5]):
        header_lines = clean(tbl[0][1]).split("\n")
        first = header_lines[0].replace("**", "")
        parts = first.rstrip(",").split(",", 1)
        inst = parts[0].strip()
        loc = parts[1].strip() if len(parts) > 1 else ""
        if inst == "University of California":
            inst, loc = "University of California, Berkeley", "USA"
        dept = header_lines[1] if len(header_lines) > 1 else None
        roles = [{"period": r[0], "title": clean(r[1])} for r in tbl[1:]]
        appts.append({
            "id": f"appt-{idx}",
            "institution": inst,
            "location": loc,
            "department": dept,
            "roles": roles,
        })
    write_yaml("appointments", appts)

    # 03 Professional Experience
    exp = []
    for idx, (period, body) in enumerate(u163[0]):
        txt = clean(body).replace("**", "")
        org, loc = [x.strip() for x in txt.split(",", 1)]
        exp.append({"id": f"exp-{idx}", "period": period, "organization": org, "location": loc, "tags": ["core"]})
    write_yaml("experience", exp)

    # 04 Publications
    def parse_pub_rows(rows, prefix):
        out = []
        for idx, (yr, cit) in enumerate(rows[1:]):
            c = clean(cit)
            c = c.replace(
                "10.1399/NuL.190572](https://www.nul-online.de/themen/landschafts-und-umweltplanung/article-8287901-201982/digitale-spuren-in-der-landschaft-.html)",
                "10.1399/NuL.190572](https://doi.org/10.1399/NuL.190572)",
            )
            c = c.replace("Landesentwicklungplan", "Landesentwicklungsplan")
            c = c.replace("Schmidt, C., Dunkel, A. Hofmann, M.", "Schmidt, C., Dunkel, A., Hofmann, M.")
            c = c.replace("Lein, M, Seiche", "Lein, M., Seiche")
            c = c.replace("publication. *Generative", "publication: *Generative")
            c = c.replace(
                "*Den Landschaftswandel gestalten!**Entwicklung und Gestaltung der Kulturlandschaften Baden-Württembergs am Beispiel der Region Ostwürttemberg.* **LUBW",
                "*Den Landschaftswandel gestalten! Entwicklung und Gestaltung der Kulturlandschaften Baden-Württembergs am Beispiel der Region Ostwürttemberg.* LUBW",
            )
            if prefix == "mono" and idx == 0:
                c = (
                    "**Dunkel, A. (2026).** *Geovisualizing Collective Perception: Integrating Opportunistic Data "
                    "into the Planning Information Cycle*, Habilitation thesis, Faculty of Environmental Sciences, "
                    "TU Dresden. [Monograph manuscript in preparation]"
                )
                yr = "2026"
            out.append({"id": f"{prefix}-{idx}", "year": yr, "citation": c, "tags": ["core"]})
        return out

    write_yaml("publications", {
        "peer_reviewed": parse_pub_rows(u163[1], "pr"),
        "coauthored": parse_pub_rows(u163[2], "co"),
        "monographs": parse_pub_rows(u163[3], "mono"),
        "data": parse_pub_rows(u163[4], "data"),
    })

    # 04 Talks
    talks = [
        {
            "id": "talk-habil-pres-2026",
            "year": "2026",
            "text": (
                "**“Geovisual Analytics for Democratic Resilience: Methodological Frontiers in Measuring Social Cohesion”**, "
                "Habilitation Scientific Trial Presentation, TU Dresden. "
                "DOI: [10.5281/zenodo.23665194](https://doi.org/10.5281/zenodo.23665194) "
                "^[slides](https://kartographie.geo.tu-dresden.de/ad/social-cohesion/)"
            ),
            "tags": ["core", "habilitation"],
        },
        {
            "id": "talk-habil-lect-2026",
            "year": "2026",
            "text": (
                "**“Principles of Good Scientific Practice in Geoinformatics: From Data Management to Reproducible Code”**, "
                "Habilitation Scientific Trial Lecture, TU Dresden. "
                "DOI: [10.5281/zenodo.23335010](https://doi.org/10.5281/zenodo.23335010) "
                "^[slides](https://kartographie.geo.tu-dresden.de/ad/reproducible-geoinformatics/)"
            ),
            "tags": ["core", "habilitation"],
        },
    ]
    for idx, (yr, body) in enumerate(u163[5][1:]):
        txt = clean(body)
        txt = txt.replace("_crowdsourced", ": crowdsourced").replace("Cartography_ Mapping", "Cartography: Mapping")
        txt = txt.replace("Guest Lecture,\nFall 2011 Colloquium", "Guest Lecture, Fall 2011 Colloquium")
        if "HaCLAthon" in txt and "hack.conference.ioer.info" not in txt:
            txt = txt.replace("^[slides]", "^[platform](https://hack.conference.ioer.info/) ^[slides]")
        talks.append({"id": f"talk-{idx}", "year": yr, "text": txt, "tags": ["core"]})
    write_yaml("talks", talks)

    # 05 Teaching
    teaching = []
    for idx, (period, body) in enumerate(u163[6][1:]):
        txt = clean(body)
        tags = ["audit-only"] if "Sports Centre" in txt else ["core"]
        teaching.append({"id": f"teach-{idx}", "period": period, "text": txt, "tags": tags})
    write_yaml("teaching", teaching)

    # 05 Theses Supervision
    theses = []
    for idx, (period, body) in enumerate(u163[7][1:]):
        txt = clean(body)
        level = "phd" if "PhD" in txt else ("diploma" if "Diploma" in txt else "master")
        inst = "University of Bonn" if "Bonn" in txt else ("IOER & TU Dresden" if "IOER" in txt else "TU Dresden")
        theses.append({
            "id": f"thesis-{idx}",
            "period": period,
            "level": level,
            "institution": inst,
            "text": txt,
            "tags": [level],
        })
    write_yaml("theses", theses)

    # 05 Service
    review_comm = []
    for idx, (period, body) in enumerate(u163[8][1:]):
        txt = clean(body).replace("PLoS one", "PLOS ONE").replace("fur Geoinformatik", "für Geoinformatik")
        review_comm.append({"id": f"rev-{idx}", "period": period, "text": txt, "tags": ["core"]})
    cont_ed = [{"id": f"ce-{idx}", "period": p, "text": clean(b), "tags": ["core"]} for idx, (p, b) in enumerate(u163[9][1:])]
    write_yaml("service", {"review_committee": review_comm, "continuing_education": cont_ed})

    # 06 Grants & PhD Projects
    def parse_grants(rows, status):
        return [
            {"id": f"grant-{status}-{i}", "period": r[0], "text": clean(r[1]), "amount": r[2], "status": status, "tags": [status]}
            for i, r in enumerate(rows)
        ]

    write_yaml("grants", {
        "awarded": parse_grants(u163[10][1:], "awarded"),
        "pending": parse_grants(u163[11], "pending"),
        "declined": parse_grants(u163[12], "declined"),
        "phd_projects": [
            {"id": f"phdproj-{i}", "period": r[0], "text": clean(r[1]), "tags": ["phd-project"]}
            for i, r in enumerate(u163[13])
        ],
    })

    # 06 Awards
    awards = []
    for idx, (yr, body) in enumerate(u163[14][1:]):
        txt = clean(body).replace("for* “", "for *“").replace("*in LAND", "* in LAND").replace("*in Landscape", "* in Landscape")
        awards.append({"id": f"award-{idx}", "year": yr, "text": txt, "tags": ["core"]})
    write_yaml("awards", awards)

    # 06 Freelance & Volunteering
    freelance = []
    for idx, (period, body) in enumerate(u163[15][1:]):
        txt = clean(body)
        highlight = any(k in txt for k in ("14,700", "5,000", "Lausitzer Surfer", "Getty Images"))
        freelance.append({
            "id": f"free-{idx}",
            "period": period,
            "text": txt,
            "highlight": highlight,
            "tags": ["core" if highlight else "minor"],
        })
    write_yaml("freelance", freelance)

    # 06 Media Coverage (clean bullet list for the 5 Digital Landscape Traces outlets)
    media = []
    for idx, (yr, body) in enumerate(u163[16][1:]):
        if idx == 0:
            txt = (
                "**Articles following the “Digital Landscape Traces” (data) publication:**\n"
                "- **kreiszeitung.de** – *“Digitales Echo” zeigt die fotogensten Orte Niedersachsens* ^[link](https://www.kreiszeitung.de/lokales/niedersachsen/digitales-echo-zeigt-die-fotogensten-orte-niedersachsens-karte-bietet-unschaetzbaren-nutzen-94179703.html)\n"
                "- **diesachsen.de** – *66 Millionen Posts zeigen beliebte Ausflugsziele* ^[link](https://www.diesachsen.de/wissensland/66-millionen-posts-zeigen-beliebte-ausflugsziele-3100385)\n"
                "- **rnd.de** – *Digitale Spuren von Touristen: Wie beliebt ist Ihr Ort in den sozialen Medien?* ^[link](https://www.rnd.de/lifestyle/digitale-spuren-wie-social-media-die-attraktivitaet-deutscher-orte-zeigt-YABGMVSOVJHYPENFR2JNSKHCYE.html)\n"
                "- **netzpolitik.org** – *Von welchen deutschen Orten posten die meisten Tourist\\*innen auf Social Media?* ^[link](https://netzpolitik.org/ticker/ticker-news-von-rnd-vom-09-02-2026/)\n"
                "- **mainpost.de** – *Vom Dom bis zur Schustergasse: Das sind die 12 beliebtesten Orte auf Social Media in Würzburg* ^[link](https://www.mainpost.de/wuerzburg/stadtwuerzburg/social-media-studie-wuerzburg-liegt-bei-posts-an-residenz-vorn-113964058)"
            )
        else:
            txt = clean(body)
        media.append({"id": f"media-{idx}", "year": yr, "text": txt, "tags": ["core"]})
    write_yaml("media", media)

    # 07 Open Source & Technology
    software = []
    for idx, (link_md, desc) in enumerate(u163[17][1:]):
        m = re.match(r"\[([^\]]+)\]\(([^)]+)\)", link_md)
        label, url = m.groups() if m else (link_md, "")
        software.append({
            "id": f"sw-{idx}",
            "label": label,
            "url": url,
            "description": clean(desc).replace("language independent", "language-independent"),
            "tags": ["core"],
        })
    write_yaml("software", software)

    print("Re-generated all 14 clean YAML files in data/")


if __name__ == "__main__":
    main()
