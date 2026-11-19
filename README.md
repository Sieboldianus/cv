# Curriculum Vitae

This is my reproducible, single-point-of-truth CV pipeline built with YAML, Python, and [Typst](https://typst.app/). It is a replacement for my Adobe InDesign workflow that I used for the past 19 yeas.

**Outputs:**

- Standard CV: [HTML](https://www.alexanderdunkel.com/cv.html), [PDF](https://www.alexanderdunkel.com/cv_alexanderdunkel.pdf)
- Full Academic Audit Log: [HTML](https://www.alexanderdunkel.com/cv_audit.html), [PDF](https://www.alexanderdunkel.com/cv_alexanderdunkel_audit.pdf)

The PDF is 100% compliant with PDF/UA-1 and WCAG 2.2.

## Concept

All career records are maintained once in `data/*.yaml` as an unredacted log. Declarative view definitions in `views/` control what gets included, omitted, or aggregated:

- **`views/audit.yaml`** renders every entry verbatim for full transparency.
- **`views/production.yaml`** filters out noise (e.g., declined grants, minor invoices) and aggregates groups (e.g., Master/Diploma theses) into computed summaries, linking back to the audit log so omissions remain verifiable.

## Structure

- `data/` - structured YAML records (`profile`, `education`, `publications`, `talks`, `grants`, etc.)
- `views/` - declarative filter & aggregation rules (`production.yaml`, `audit.yaml`)
- `templates/` - `cv.typ` (Typst A4 layout) and `cv.html.j2` (minimal responsive HTML)
- `scripts/build.py` - validates URLs, resolves views into `dist/*.json`, compiles PDFs and HTML into `site/`
- `.gitlab-ci.yml` - builds and deploys via [typst-cv](https://github.com/Sieboldianus/typst-cv)

## Local Build

Requires Docker and the builder image from [Sieboldianus/typst-cv](https://github.com/Sieboldianus/typst-cv):

```bash
docker build -t typst-cv .
# ... switch repos
docker run --rm -v "$(pwd):/work" -w /work \
  typst-cv \
  python3 scripts/build.py
```

Outputs are written to `site/`.

## License

Code and templates: MIT / CC0. Personal CV data (`data/*.yaml`): © Alexander Dunkel.