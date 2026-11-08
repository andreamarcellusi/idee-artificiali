#!/usr/bin/env python3
"""Genera il sito statico in docs/ a partire da content/, assets/ e templates/.

Uso:  python build.py
Non servono altre dipendenze oltre a: pyyaml, markdown, jinja2.
"""
import datetime as dt
import csv
import html
import io
import pathlib
import re
import shutil

import markdown
import openpyxl
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


URL_RE = re.compile(r"(https?://[^\s<]+[^\s<.,;:!?)\]])")


def linkedin_html(text):
    """Testo del post così com'è su LinkedIn: a capo conservati, link cliccabili, niente markdown."""
    paras = [x for x in re.split(r"\n\s*\n", text.strip()) if x.strip()]
    out = []
    for par in paras:
        lines = [html.escape(l.rstrip()) for l in par.split("\n")]
        lines = [URL_RE.sub(r'<a href="\1" target="_blank" rel="noopener">\1</a>', l) for l in lines]
        out.append("<p>" + "<br>".join(lines) + "</p>")
    return "\n".join(out)


def date_it(d):
    d = dt.date.fromisoformat(str(d))
    return f"{d.day:02d} {MESI[d.month - 1]} {d.year}"


def main():
    site = yaml.safe_load((CONTENT / "site.yml").read_text(encoding="utf-8"))
    base = site["base_url"].rstrip("/")
    site_url = site.get("site_url", "https://andreamarcellusi.github.io" + base)
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]))
    env.filters['minuscola'] = lambda x: x[:1].lower() + x[1:] if x[1:2].islower() else x
    env.globals.update(site=site, base=base, site_url=site_url, build_date=date_it(dt.date.today()), build_ver=dt.datetime.now().strftime('%Y%m%d%H%M'))

    def carica(cartella, sezione, tipo, code):
      out = []
      for path in sorted((CONTENT / cartella).glob("*.md")):
          p = read_md(path)
          if p.get("bozza"):
              continue  # non pubblicata finché bozza: true
          p["slug"] = re.sub(r"^\d+-", "", path.stem)
          p["date_it"] = date_it(p["date"])
          p["allegato_label"] = ALLEGATI.get(p.get("allegato", "nessuno"), p.get("allegato"))
          if p.get("allegato", "nessuno") == "nessuno" and p.get("allegato_linkedin"):
              p["allegato_label"] = f'{p["allegato_linkedin"]} su LinkedIn, qui non ancora'
          if p.get("allegato") == "immagine" and not (ASSETS / "immagini" / p["immagine"]).exists():
              raise SystemExit(f"{path}: immagine '{p['immagine']}' assente in assets/immagini/")
          if p.get("testo") != "da importare" and p["body_raw"]:
              p["testo"] = "importato"
              p["body_html"] = linkedin_html(p["body_raw"])
          if p.get("allegato") == "carosello":
              pages = sorted((ASSETS / "caroselli" / p["carosello"]).glob("p-*.jpg"))
              if not pages:
                  raise SystemExit(f"{path}: carosello '{p['carosello']}' senza pagine in assets/caroselli/")
              p["pages"] = [x.name for x in pages]
              p["allegato_label"] = f"carosello · {len(pages)} pagine"
          p["sezione"], p["tipo"], p["code"] = sezione, tipo, code(p["n"])
          out.append(p)
      return out

    idee = carica("idee", "idee", "Idea", lambda n: f"{n:02d}")
    preistoria = carica("preistoria", "preistoria", "Preistoria", lambda n: f"P{n}")
    for p in idee + preistoria:
        fonti = " ".join(f.get("titolo", "") for f in (p.get("fonti") or []))
        p["search_text"] = re.sub(r"\s+", " ", f'{p["title"]} {p["summary"]} {p["body_raw"]} {fonti} {" ".join(site["temi"][t] for t in p["temi"])}')
    idee.sort(key=lambda x: (str(x["date"]), x["n"]), reverse=True)
    # rete: nodi e collegamenti (espliciti = strong; stesso tema = weak)
    by_slug = {p["slug"]: p for p in idee}
    def short(t, n=26):
        t = re.split(r"[:.]", t)[0]
        return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"
    nodes = [{"id": p["slug"], "n": f'{p["n"]:02d}', "title": p["title"], "label": p.get("etichetta") or short(p["title"]), "date": p["date_it"], "tema": p["temi"][0], "url": f'{base}/idee/{p["slug"]}/'} for p in idee]
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
    # sintesi testuale della rete, ricalcolata a ogni build
    deg = {p["slug"]: 0 for p in idee}
    for l in glinks:
        if l["strong"]:
            deg[l["source"]] += 1; deg[l["target"]] += 1
    conta = {k: sum(1 for p in idee if k in p["temi"]) for k in site["temi"]}
    temi_ord = [(site["temi"][k], n) for k, n in sorted(conta.items(), key=lambda x: -x[1]) if n]
    hub = sorted(idee, key=lambda p: (-deg[p["slug"]], str(p["date"])))[:2]
    sintesi = {
        "n": len(idee), "dal": date_it(min(str(p["date"]) for p in idee)), "al": date_it(max(str(p["date"]) for p in idee)),
        "temi": temi_ord, "hub": [(p, deg[p["slug"]]) for p in hub if deg[p["slug"]]],
        "ultime": idee[:2],
        "per_tema": [dict(k=k, nome=site["temi"][k], n=conta[k], desc=(site.get("temi_descrizioni") or {}).get(k, ""),
                          idee=sorted([p for p in idee if k in p["temi"]], key=lambda p: (-deg[p["slug"]], str(p["date"])))[:3])
                     for k, _ in sorted(conta.items(), key=lambda x: -x[1]) if conta[k]], "isolate": sum(1 for v in deg.values() if v == 0),
        "novita": sorted(site.get("novita") or [], key=lambda x: str(x["data"]), reverse=True)[:3],
    }
    for nv in sintesi["novita"]:
        nv["data_it"] = date_it(nv["data"])
    tema_colors = site.get("tema_colors", {})
    for i, p in enumerate(idee):
        p["next"] = idee[i - 1] if i > 0 else None       # più recente
        p["prev"] = idee[i + 1] if i + 1 < len(idee) else None  # più vecchia

    preistoria.sort(key=lambda x: (str(x["date"]), x["n"]), reverse=True)
    for i, p in enumerate(preistoria):
        p["next"] = preistoria[i - 1] if i > 0 else None
        p["prev"] = preistoria[i + 1] if i + 1 < len(preistoria) else None

    # I numeri: dataset
    datasets = []
    for f in sorted((CONTENT / "numeri").glob("*.yml")):
        ds = yaml.safe_load(f.read_text(encoding="utf-8")); ds["slug"] = re.sub(r"^\d+-", "", f.stem)
        cartella = ASSETS / "numeri" / ds["slug"]
        for fi in ds["files"]:
            pth = cartella / fi["file"]
            if not pth.exists():
                raise SystemExit(f"{f}: file {fi['file']} assente in {cartella}")
            kb = pth.stat().st_size / 1024
            fi["peso"] = f"{kb:.0f} KB" if kb < 1024 else f"{kb/1024:.1f} MB"
            fi["tipo"] = pth.suffix[1:].upper()
            fi["url"] = f"{base}/assets/numeri/{ds['slug']}/{fi['file']}"
            if pth.suffix == ".csv":
                txt = pth.read_text(encoding="utf-8-sig"); sep = ";" if txt.split("\n")[0].count(";") > txt.split("\n")[0].count(",") else ","
                righe = list(csv.reader(io.StringIO(txt), delimiter=sep))
                hdr = next((i for i, r in enumerate(righe) if sum(1 for c in r if c.strip()) >= 3), 0)
                fi["colonne"] = [c for c in righe[hdr] if c.strip()]; fi["righe"] = len([r for r in righe[hdr + 1:] if any(c.strip() for c in r)])
            elif pth.suffix == ".xlsx":
                wb = openpyxl.load_workbook(pth, read_only=True); fi["fogli"] = wb.sheetnames
        ds["idee_obj"] = [by_slug[x] for x in ds.get("idee", []) if x in by_slug]
        for p in ds["idee_obj"]:
            p.setdefault("datasets", []).append(ds)
        ds["data_it"] = date_it(ds["data"])
        datasets.append(ds)

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
    genesi["paragrafi"] = [x.strip() for x in genesi["body_raw"].split("\n\n") if x.strip()]
    (OUT / "index.html").write_text(env.get_template("index.html").render(idee=idee, genesi=genesi, n_caroselli=n_car, graph=graph, sintesi=sintesi, tema_colors=tema_colors, current="/"), encoding="utf-8")
    (OUT / "idee").mkdir(exist_ok=True)
    (OUT / "idee" / "index.html").write_text(env.get_template("idee.html").render(idee=idee, page_title="Le idee", current="/idee/"), encoding="utf-8")

    (OUT / "preistoria").mkdir()
    (OUT / "preistoria" / "index.html").write_text(env.get_template("preistoria.html").render(idee=preistoria, page_title="La preistoria", current="/idee/"), encoding="utf-8")
    for p in idee + preistoria:
        d = OUT / p["sezione"] / p["slug"]
        d.mkdir(parents=True)
        og = None
        if p.get("allegato") == "carosello":
            og = f"{site_url}/assets/caroselli/{p['carosello']}/{p['pages'][0]}"
        elif p.get("allegato") == "immagine":
            og = f"{site_url}/assets/immagini/{p['immagine']}"
        (d / "index.html").write_text(
            env.get_template("idea.html").render(p=p, page_title=p["title"], description=p["summary"], og_image=og, current=None),
            encoding="utf-8")

    for name in ["ripensamenti", "voci", "istruzioni"]:
        s = read_md(CONTENT / f"{name}.md")
        d = OUT / name
        d.mkdir()
        (d / "index.html").write_text(
            env.get_template("section.html").render(s=s, page_title=s["title"], description=s.get("intro"), current=f"/{name}/"),
            encoding="utf-8")

    s = read_md(CONTENT / "numeri.md")
    (OUT / "numeri").mkdir()
    (OUT / "numeri" / "index.html").write_text(env.get_template("numeri.html").render(s=s, datasets=datasets, page_title=s["title"], description=s.get("intro"), current="/numeri/"), encoding="utf-8")
    for ds in datasets:
        d = OUT / "numeri" / ds["slug"]; d.mkdir()
        (d / "index.html").write_text(env.get_template("dataset.html").render(ds=ds, page_title=ds["titolo"], description=ds["sintesi"], current="/numeri/"), encoding="utf-8")

    print(f"{len(datasets)} dataset")
    print(f"ok: {len(idee)} idee, {len(preistoria)} preistoria, {n_car} caroselli -> {OUT}")


if __name__ == "__main__":
    main()
