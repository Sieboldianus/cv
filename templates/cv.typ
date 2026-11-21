#let data = json("/" + sys.inputs.at("data", default: "dist/resolved_production.json"))

#let color-link = rgb("#1e549f")
#let color-dot = luma(117)
#let color-footer = luma(128)
#let color-badge-bg = rgb("#e4e5e8")

#let dot-stroke = (paint: color-dot, thickness: 0.5pt, dash: (array: (0.6pt, 1.8pt)))

#let render-inline(line) = {
  let tokens = line.matches(regex("(\\^?\\[[^\\]]+\\]\\([^)]+\\)|\\*\\*\\*(?:[^*\\\\]|\\\\.)+\\*\\*\\*|\\*\\*(?:[^*\\\\]|\\\\.)+\\*\\*|\\*(?:[^*\\\\]|\\\\.)+\\*)"))
  let cursor = 0
  for m in tokens {
    if m.start > cursor {
      [#line.slice(cursor, m.start).replace("\\*", "*")]
    }
    let tok = m.text
    if tok.starts-with("^[") {
      let inner = tok.slice(2, tok.len() - 1)
      let idx = inner.position("](")
      let lbl = inner.slice(0, idx)
      let url = inner.slice(idx + 2)
      super(typographic: false, size: 6.2pt)[#link(url)[#underline(text(fill: color-link)[\[#lbl\]])]]
    } else if tok.starts-with("[") {
      let inner = tok.slice(1, tok.len() - 1)
      let idx = inner.position("](")
      let lbl = inner.slice(0, idx)
      let url = inner.slice(idx + 2)
      link(url)[#underline(text(fill: color-link)[#lbl])]
    } else if tok.starts-with("***") {
      strong(emph(tok.slice(3, tok.len() - 3).replace("\\*", "*")))
    } else if tok.starts-with("**") {
      strong(tok.slice(2, tok.len() - 2).replace("\\*", "*"))
    } else if tok.starts-with("*") {
      emph(tok.slice(1, tok.len() - 1).replace("\\*", "*"))
    }
    cursor = m.end
  }
  if cursor < line.len() {
    [#line.slice(cursor).replace("\\*", "*")]
  }
}

#let rich(s) = {
  if s == none or s == "" { return [] }
  let lines = s.split("\n")
  for (i, line) in lines.enumerate() {
    if line.starts-with("- ") {
      if i > 0 { v(2pt, weak: true) }
      grid(columns: (10pt, 1fr), row-gutter: 2pt, [•], render-inline(line.slice(2)))
    } else {
      if i > 0 { linebreak() }
      render-inline(line)
    }
  }
}

#let dt-parts = data.meta.iso_date.split("T")
#let d = dt-parts.at(0).split("-").map(int)
#let t = dt-parts.at(1).split(":").map(int)

#set document(
  title: data.profile.name + " - Curriculum Vitae" + if data.meta.view == "audit" { " (Audit Log)" } else { "" },
  author: data.profile.name,
  description: "Curriculum Vitae of Dr.-Ing. habil. Alexander Dunkel — Senior Scientist, Geovisual Analytics, Cartography, Spatial Data Science." + if data.meta.commit_sha != "" { " [Commit #" + data.meta.commit_sha + "]" } else { "" },
  keywords: ("Curriculum Vitae", "Geovisual Analytics", "Cartography", "Spatial Data Science", "GIS", "IOER", "TU Dresden"),
  date: datetime(year: d.at(0), month: d.at(1), day: d.at(2), hour: t.at(0), minute: t.at(1), second: t.at(2)),
)

#set page(
  paper: "a4",
  margin: (left: 56.5pt, right: 36pt, top: 36pt, bottom: 52pt),
  footer-descent: 16pt,
  footer: context {
    set text(font: "EB Garamond", size: 7pt, fill: color-footer)
    move(dx: -20.5pt, box(width: 100% + 20.5pt)[
      #upper[Last update: #data.meta.last_update]
      #h(1fr)
      #upper[Page #counter(page).display("1 of 1", both: true)]
    ])
  }
)

#set text(font: "EB Garamond", size: 10pt, fill: black, lang: "en")
#set par(leading: 5.8pt, spacing: 8pt)
#set grid.cell(breakable: false)

// PDF Bookmarks
#show heading.where(level: 1): it => {
  v(16pt, weak: true)
  block(sticky: true, below: 9pt)[
    #text(size: 14pt, weight: "bold")[#it.body]
  ]
}

#let section-heading(num, title) = heading(level: 1, bookmarked: true)[#num #upper(title)]

#let sub-grid(title, subtitle: none, cols: (83.5pt, 1fr), rows) = {
  if rows.len() == 0 { return }
  grid(
    columns: cols,
    inset: (x: 6pt, y: 5.5pt),
    stroke: none,
    grid.header(
      grid.cell(colspan: cols.len(), stroke: (bottom: dot-stroke), align: bottom)[
        #text(weight: "bold")[#upper(title)]
        #if subtitle != none [ #text(weight: "regular")[#subtitle]]
      ]
    ),
    ..rows.flatten()
  )
  v(6pt)
}

#show heading.where(level: 2): it => {
  set text(size: 10pt, weight: "regular")
  block(
    width: 100%,
    sticky: true,
    above: 4pt,
    below: 0pt,
    inset: (x: 6pt, top: 6pt, bottom: 5.5pt),
    stroke: (bottom: dot-stroke),
  )[#it.body]
}

#let sub-grid(title, subtitle: none, cols: (83.5pt, 1fr), rows) = {
  if rows.len() == 0 { return }
  heading(level: 2, bookmarked: true)[
    #strong(upper(title))#if subtitle != none [ #subtitle]
  ]
  grid(
    columns: cols,
    inset: (x: 6pt, y: 5.5pt),
    stroke: none,
    ..rows.flatten()
  )
  v(6pt)
}

// Dekoratives CV-Badge als PDF-Artefakt markieren:
#place(top + right, dx: 0pt, dy: 0pt)[
  #pdf.artifact[
    #box(width: 74.4pt, height: 46.8pt, fill: color-badge-bg, align(center + horizon)[
      #text(size: 40pt, weight: "bold", fill: white, tracking: 0.1em)[CV]
    ])
  ]
]

// --- PAGE 1 HEADER & TOP-RIGHT CV BADGE ---
#place(top + right, dx: 0pt, dy: 0pt)[
  #box(width: 74.4pt, height: 46.8pt, fill: color-badge-bg, align(center + horizon)[
    #text(size: 40pt, weight: "bold", fill: white, tracking: 0.1em)[CV]
  ])
]

#v(103pt)

#text(size: 15pt, weight: "bold")[#upper(data.profile.name)] \
#data.profile.degrees

#v(14pt)
#text(size: 11pt, weight: "bold")[#data.profile.role] \
#data.profile.affiliation_line1 \
#data.profile.affiliation_line2

#v(10pt)
#grid(
  columns: (42pt, auto),
  row-gutter: 3.5pt,
  [Mail:], [#link("mailto:" + data.profile.emails.at(0))[#data.profile.emails.at(0)] \ #link("mailto:" + data.profile.emails.at(1))[#data.profile.emails.at(1)]],
  [Web:], [#link("https://" + data.profile.web)[#underline(text(fill: color-link)[#data.profile.web])]],
  [P:], [#data.profile.phone],
  [ORCID:], [#link("https://orcid.org/" + data.profile.orcid)[#underline(text(fill: color-link)[#data.profile.orcid])]],
)

#v(8pt)

// --- 01 EDUCATION ---
#section-heading("01", "Education")
#grid(
  columns: (67.2pt, 266.4pt),
  inset: (x: 4pt, y: 5.5pt),
  stroke: none,
  ..data.education.map(e => (
    [#e.period],
    [#strong(e.institution), #e.country \ #rich(e.details)]
  )).flatten()
)

// --- 02 ACADEMIC APPOINTMENTS ---
#section-heading("02", "Academic Appointments")
#for (idx, inst) in data.appointments.enumerate() {
  let is-last = idx == data.appointments.len() - 1
  grid(
    columns: (67.16pt, 435.64pt),
    inset: (x: 4pt, y: 5.5pt),
    stroke: none,
    grid.header(
      [],
      [
        #strong(inst.institution), #inst.location
        #if inst.at("department", default: none) != none [\ #inst.department]
      ]
    ),
    ..inst.roles.enumerate().map(((r_idx, r)) => {
      let row-stroke = if (not is-last and r_idx == inst.roles.len() - 1) { (bottom: dot-stroke) } else { none }
      (grid.cell(stroke: row-stroke)[#r.period], grid.cell(stroke: row-stroke)[#rich(r.title)])
    }).flatten()
  )
  v(4pt)
}

// --- 03 PROFESSIONAL EXPERIENCE ---
#block(breakable: false)[
  #section-heading("03", "Professional Experience")
  #grid(
    columns: (83.5pt, 1fr),
    inset: (x: 6pt, y: 5.5pt),
    stroke: none,
    ..data.experience.map(e => ([#e.period], [#strong(e.organization), #e.location])).flatten()
  )
]

// --- 04 SCHOLARLY WORK ---
#section-heading("04", "Scholarly Work")
#sub-grid("Peer Reviewed", subtitle: "(first-authored)", data.publications.peer_reviewed.map(p => ([#p.year], [#rich(p.citation)])))
#sub-grid("Articles & Conference Papers", subtitle: "(co-authored)", data.publications.coauthored.map(p => ([#p.year], [#rich(p.citation)])))
#sub-grid("Monographs, Book Chapters & Articles", data.publications.monographs.map(p => ([#p.year], [#rich(p.citation)])))
#sub-grid("Data Publications", data.publications.data.map(p => ([#p.year], [#rich(p.citation)])))
#sub-grid("Invited Lectures, Presentations, Symposia", data.talks.map(t => ([#t.year], [#rich(t.text)])))

// --- 05 TEACHING ---
#section-heading("05", "Teaching")
#sub-grid("Lectures and Workshops", data.teaching.map(t => ([#t.period], [#rich(t.text)])))
#sub-grid("Thesis Supervision", data.theses.map(t => ([#t.period], [#rich(t.text)])))
#sub-grid("Review and Committee Work", data.service.review_committee.map(s => ([#s.period], [#rich(s.text)])))
#sub-grid("Continuing Education", data.service.continuing_education.map(s => ([#s.period], [#rich(s.text)])))

// --- 06 PROJECTS, GRANTS AND RECOGNITION ---
#section-heading("06", "Projects, Grants and Recognition")
#sub-grid("Project Application / Grants", cols: (83.5pt, 324.5pt, 94.45pt), data.grants.awarded.map(g => ([#g.period], [#rich(g.text)], [#g.amount])))

#if data.grants.pending.len() > 0 {
  [Submitted grant applications (under review):]
  grid(
    columns: (83.5pt, 324.5pt, 94.45pt),
    inset: (x: 6pt, y: 5.5pt),
    stroke: (top: dot-stroke),
    ..data.grants.pending.map(g => (grid.cell(stroke: none)[#g.period], grid.cell(stroke: none)[#rich(g.text)], grid.cell(stroke: none)[#g.amount])).flatten()
  )
}

#if data.grants.declined.len() > 0 {
  [Declined Grants:]
  grid(
    columns: (83.5pt, 324.5pt, 94.45pt),
    inset: (x: 6pt, y: 5.5pt),
    stroke: none,
    ..data.grants.declined.map(g => (grid.cell(stroke: (bottom: dot-stroke))[#g.period], grid.cell(stroke: (bottom: dot-stroke))[#rich(g.text)], grid.cell(stroke: (bottom: dot-stroke))[#g.amount])).flatten()
  )
}

#if data.grants.phd_projects.len() > 0 {
  [Project Work (PhD-phase):]
  grid(
    columns: (83.5pt, 324.5pt, 94.45pt),
    inset: (x: 6pt, y: 5.5pt),
    stroke: none,
    ..data.grants.phd_projects.map(g => (grid.cell(stroke: (bottom: dot-stroke))[#g.period], grid.cell(stroke: (bottom: dot-stroke))[#rich(g.text)], grid.cell(stroke: (bottom: dot-stroke))[])).flatten()
  )
}

#sub-grid("Fellowships and Awards", data.awards.map(a => ([#a.year], [#rich(a.text)])))
#sub-grid("Freelance & Contract Work, Volunteering", data.freelance.map(f => ([#f.period], [#rich(f.text)])))
#sub-grid("Magazine / Media Coverage, Outreach", data.media.map(m => ([#m.year], [#rich(m.text)])))

// --- 07 OPEN SOURCE AND TECHNOLOGY ---
#section-heading("07", "Open Source and Technology")
#sub-grid("Projects, Packages and Frameworks", cols: (145.2pt, 357.6pt), data.software.map(s => (
  [#link(s.url)[#underline(text(fill: color-link)[#s.label])]],
  [#rich(s.description)]
)))

// --- CLOSING BLOCK ---
#v(24pt)
#block(breakable: false)[
  #pad(left: 151.2pt, right: 60pt)[
    #rich(data.profile.closing_text)
    #if data.meta.closing_note != "" [
      #v(10pt)
      #rich(data.meta.closing_note)
    ]
  ]
]
