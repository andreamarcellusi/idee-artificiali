#!/usr/bin/env python3
"""Genera il sito statico in docs/ a partire da content/, assets/ e templates/.

Uso:  python build.py
Non servono altre dipendenze oltre a: pyyaml, markdown, jinja2.
"""
import datetime as dt
import pathlib
import re
import shutil

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = pathlib.Path(__file__).parent
CONTENT, ASSETS, TEMPLATES, OUT = ROOT / "content", ROOT / "assets", ROOT / "templates", ROOT / "docs"

MESI = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]
ALLEGATI = {"carosello": "carosello", "immagine": "immagine", "video": "video", "nessuno": "nessun allegato"}


def read_md(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        raise SystemExit(f"{path}: manca il blocco --- iniziale")
    fm = yaml.safe_load(m.group(1)) or {}
    body = re.sub(r"<!--.*?-->", "", m.group(2), flags=re.S).strip()
    fm["body_html"] = markdown.markdown(body, extensions=["extra", "smarty"]) if body else ""
    fm["body_raw"] = body
    return fm


def date_it(d):
    d = dt.date.fromisoformat(str(d))
    return f"{d.day:02d} {MESI[d.month - 1]} {d.year}"


def main():
    site = yaml.safe_load((CONTENT / "site.yml").read_text(encoding="utf-8"))
    base = site["base_url"].rstrip("/")
    site_url = site.get("site_url", "https://andreamarcellusi.github.io" + base)
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]))
    env.globals.update(site=site, base=base, site_url=site_url, build_date=date_it(dt.date.today()))

    # Idee
    idee = []
    for path in sorted((CONTENT / "idee").glob("*.md")):
        p = read_md(path)
        if p.get("bozza"):
            continue  # non pubblicata finché bozza: true
        p["slug"] = re.sub(r"^\d+-", "", path.stem)
        p["date_it"] = date_it(p["date"])
        p["allegato_label"] = ALLEGATI.get(p.get("allegato", "nessuno"), p.get("allegato"))
        if p.get("testo") != "da importare" and p["body_raw"]:
            p["testo"] = "importato"
        if p.get("allegato") == "carosello":
            pages = sorted((ASSETS / "caroselli" / p["carosello"]).glob("p-*.jpg"))
            if not pages:
                raise SystemExit(f"{path}: carosello '{p['carosello']}' senza pagine in assets/caroselli/")
            p["pages"] = [x.name for x in pages]
            p["allegato_label"] = f"carosello · {len(pages)} pagine"
        idee.append(p)
    for p in idee:
        fonti = " ".join(f.get("titolo", "") for f in (p.get("fonti") or []))
        p["search_text"] = re.sub(r"\s+", " ", f'{p["title"]} {p["summary"]} {p["body_raw"]} {fonti} {" ".join(site["temi"][t] for t in p["temi"])}')
    idee.sort(key=lambda x: (str(x["date"]), x["n"]), reverse=True)
    # rete: nodi e collegamenti (espliciti = strong; stesso tema = weak)
    by_slug = {p["slug"]: p for p in idee}
    def short(t, n=26):
        t = re.split(r"[:.]", t)[0]
        return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"
    nodes = [{"id": p["slug"], "n": f'{p["n"]:02d}', "title": p["title"], "label": short(p["title"]), "date": p["date_it"], "tema": p["temi"][0], "url": f'{base}/idee/{p["slug"]}/'} for p in idee]
    seen, glinks = set(), []
    for p in idee:
        for s in p.get("collegata_a") or []:
            if s not in by_slug:
                raise SystemExit(f'{p["slug"]}: collegata_a "{s}" non esiste')
            k = tuple(sorted((p["slug"], s)))
            if k not in seen:
                seen.add(k); glinks.append({"source": k[0], "target": k[1], "strong": True})
    for i, a in enumerate(idee):
        for bq in idee[i + 1:]:
            if set(a["temi"]) & set(bq["temi"]):
                k = tuple(sorted((a["slug"], bq["slug"])))
                if k not in seen:
                    seen.add(k); glinks.append({"source": k[0], "target": k[1], "strong": False})
    graph = {"nodes": nodes, "links": glinks}
    tema_colors = site.get("tema_colors", {})
    for i, p in enumerate(idee):
        p["next"] = idee[i - 1] if i > 0 else None       # più recente
        p["prev"] = idee[i + 1] if i + 1 < len(idee) else None  # più vecchia

    # Output
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    (OUT / ".nojekyll").write_text("")
    if site.get("site_url","").startswith("https://") and "github.io" not in site["site_url"]:
        (OUT / "CNAME").write_text(site["site_url"].split("//")[1].strip("/") + "\n")
    shutil.copytree(ASSETS, OUT / "assets")
    shutil.copy(TEMPLATES / "style.css", OUT / "style.css")
    shutil.copy(TEMPLATES / "favicon.svg", OUT / "favicon.svg")

    n_car = sum(1 for p in idee if p.get("allegato") == "carosello")
    genesi = read_md(CONTENT / "genesi.md")
    (OUT / "index.html").write_text(env.get_template("index.html").render(idee=idee, genesi=genesi, n_caroselli=n_car, graph=graph, tema_colors=tema_colors, current="/"), encoding="utf-8")
    (OUT / "idee").mkdir(exist_ok=True)
    (OUT / "idee" / "index.html").write_text(env.get_template("idee.html").render(idee=idee, page_title="Le idee", current="/idee/"), encoding="utf-8")

    for p in idee:
        d = OUT / "idee" / p["slug"]
        d.mkdir(parents=True)
        og = None
        if p.get("allegato") == "carosello":
            og = f"{site_url}/assets/caroselli/{p['carosello']}/{p['pages'][0]}"
        elif p.get("allegato") == "immagine":
            og = f"{site_url}/assets/immagini/{p['immagine']}"
        (d / "index.html").write_text(
            env.get_template("idea.html").render(p=p, page_title=p["title"], description=p["summary"], og_image=og, current=None),
            encoding="utf-8")

    for name in ["ripensamenti", "numeri", "voci", "istruzioni"]:
        s = read_md(CONTENT / f"{name}.md")
        d = OUT / name
        d.mkdir()
        (d / "index.html").write_text(
            env.get_template("section.html").render(s=s, page_title=s["title"], description=s.get("intro"), current=f"/{name}/"),
            encoding="utf-8")

    print(f"ok: {len(idee)} idee, {n_car} caroselli -> {OUT}")


if __name__ == "__main__":
    main()
