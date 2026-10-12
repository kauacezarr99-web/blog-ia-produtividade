#!/usr/bin/env python
"""stdlib-only static site generator for an affiliate content site.
Render:  python build.py   (reads ./content/*.md -> ./public/)"""

import json, os, re, html, datetime, urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT, PUBLIC = os.path.join(ROOT, "content"), os.path.join(ROOT, "public")
CONFIG = os.path.join(ROOT, "config.json")


def load_config():
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)


def slugify(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def parse_article(path):
    raw = open(path, encoding="utf-8").read()
    fm, body = {}, raw
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            for ln in raw[3:end].split("\n"):
                if ":" in ln:
                    k, v = ln.split(":", 1)
                    v = v.strip()
                    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                        v = v[1:-1]
                    fm[k.strip()] = v
            body = raw[end + 4:].strip()
    return fm, body


def md_to_html(md):
    # minimal: #/##/###, >, -/*, 1., ```code```, **bold**, *em*, `code`, [text](url), ---
    lines, out, in_ul, in_ol = md.split("\n"), [], False, False

    def inline(t):
        t = html.escape(t)
        t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
        t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", t)
        t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
        return t

    def close():
        nonlocal in_ul, in_ol
        if in_ul: out.append("</ul>"); in_ul = False
        if in_ol: out.append("</ol>"); in_ol = False

    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip(): close(); i += 1; continue
        if line.startswith("```"):
            close(); code = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(html.escape(lines[i])); i += 1
            i += 1; out.append("<pre><code>" + "\n".join(code) + "</code></pre>"); continue
        if line.startswith("### "): close(); out.append("<h3>" + inline(line[4:]) + "</h3>")
        elif line.startswith("## "): close(); out.append("<h2>" + inline(line[3:]) + "</h2>")
        elif line.startswith("# "): close(); out.append("<h1>" + inline(line[2:]) + "</h1>")
        elif line.startswith("> "): close(); out.append("<blockquote>" + inline(line[2:]) + "</blockquote>")
        elif re.match(r"^\s*[-*] ", line):
            if not in_ul: close(); out.append("<ul>"); in_ul = True
            out.append("<li>" + inline(re.sub(r"^\s*[-*] ", "", line)) + "</li>")
        elif re.match(r"^\s*\d+\. ", line):
            if not in_ol: close(); out.append("<ol>"); in_ol = True
            out.append("<li>" + inline(re.sub(r"^\s*\d+\. ", "", line)) + "</li>")
        elif line.startswith("---"): close(); out.append("<hr>")
        else: close(); out.append("<p>" + inline(line) + "</p>")
        i += 1
    close()
    return "\n".join(out)


def expand_affiliate(text, cfg):
    tag = cfg.get("amazon_tag", "").strip()

    def amz(m):
        kw = m.group(1).strip()
        base = f"https://www.amazon.com/s?k={urllib.parse.quote(kw)}"
        if tag:
            return f'<a href="{base}&tag={html.escape(tag)}">{html.escape(kw)}</a>'
        else:
            return f'<a href="{base}">{html.escape(kw)}</a>'

    # Replace {{AMAZON:Keyword}} with clickable link
    text = re.sub(r"\{\{AMAZON:([^}]+)\}\}", amz, text)

    # Legacy support: if any raw placeholder remains without expansion, ensure no leak
    return text


def render(title, body, cfg, desc=""):
    site_name = html.escape(cfg.get("site_name", "Site"))
    return f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{html.escape(desc)}"><title>{html.escape(title)} - {site_name}</title>
<style>
body{{font:16px/1.7 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:760px;margin:auto;padding:30px 20px;color:#1a1a1a;background:#fff}}
h1,h2,h3{{line-height:1.25;color:#111}}
a{{color:#0a66c2;text-decoration:none}}
a:hover{{text-decoration:underline}}
code{{background:#f0f0f0;padding:1px 5px;border-radius:3px;font-size:14px}}
pre{{background:#0d1117;color:#c9d1d9;padding:14px;border-radius:6px;overflow:auto}}
blockquote{{border-left:3px solid #0a66c2;margin:16px 0;padding:4px 16px;color:#555;background:#f8f9fa}}
header{{border-bottom:1px solid #eee;padding-bottom:16px;margin-bottom:24px}}
footer{{margin-top:40px;padding-top:16px;border-top:1px solid #eee;font-size:13px;color:#666}}
.badge{{display:inline-block;background:#eef6ff;color:#0a66c2;padding:2px 8px;border-radius:12px;font-size:12px;margin-bottom:8px}}
</style></head>
<body>
<header><a href="index.html" style="font-weight:700;color:#111;text-decoration:none">{site_name}</a><br><span style="color:#666;font-size:14px">{html.escape(cfg.get("tagline",""))}</span></header>
<main>{body}</main>
<footer>
<p><strong>Aviso de afiliado:</strong> Este site contém links de afiliado. Se você comprar através de um link, posso ganhar comissão sem custo extra para você. (<a href="disclosure.html">política completa</a>)</p>
<p style="font-size:12px;color:#999">&copy; {datetime.date.today().year} {site_name}. Conteúdo original sobre ferramentas de IA para produtividade.</p>
</footer>
</body></html>"""


def main():
    cfg = load_config()
    site = cfg.get("site_url", "").rstrip("/")
    os.makedirs(PUBLIC, exist_ok=True)
    arts = []
    for fn in sorted(os.listdir(CONTENT)):
        if not fn.endswith(".md"):
            continue
        if fn.startswith("_"):
            continue  # internal files (e.g. _topic-queue.md) — skip
        fm, body = parse_article(os.path.join(CONTENT, fn))
        title = fm.get("title", fn[:-3])
        slug = fm.get("slug", slugify(title))
        desc = fm.get("description", title)
        date = fm.get("date", "")
        # expand affiliate BEFORE md conversion so link html survives inline escaping correctly
        # we convert markdown after expansion: expand produces <a> tags that md_to_html will escape if done after
        # So we do: expand -> then md_to_html will escape the <a> unless we handle it.
        # Workaround: placeholder then restore
        # Instead, expand inside md_to_html inline step is not available, so we do text replacement after md_to_html for a special marker
        # Simpler: do expand that produces markdown link syntax, then let md_to_html convert
        # But current expand returns HTML <a> directly. To keep it unescaped, we inject before md_to_html and protect it.
        # Approach: use a token that md_to_html inline won't escape: we temporarily replace {{AMAZON:X}} with <<<AMZ:X>>> then post-process
        protected = re.sub(r"\{\{AMAZON:([^}]+)\}\}", r"<<<AMZ:\1>>>", body)
        html_body = md_to_html(protected)
        # now replace protected tokens with real links
        def restore(m):
            kw = m.group(1).strip()
            tag = cfg.get("amazon_tag", "").strip()
            base = f"https://www.amazon.com/s?k={urllib.parse.quote(kw)}"
            href = f"{base}&tag={urllib.parse.quote(tag)}" if tag else base
            # href needs html escaping for & -> &amp; is ok in HTML, but we keep raw & and let html parser handle
            # Use &amp; for valid HTML
            href_esc = html.escape(href)
            return f'<a href="{href_esc}">{html.escape(kw)}</a>'
        html_body = re.sub(r"&lt;&lt;&lt;AMZ:([^&]+)&gt;&gt;&gt;", restore, html_body)
        # also handle case where md_to_html didn't escape <<< >>> (if no escaping happened)
        html_body = re.sub(r"<<<AMZ:([^>]+)>>>", restore, html_body)

        page = render(title, html_body, cfg, desc)
        open(os.path.join(PUBLIC, slug + ".html"), "w", encoding="utf-8").write(page)
        arts.append({"title": title, "slug": slug, "desc": desc, "date": date})
        print("  built:", slug + ".html")

    # index
    arts_sorted = sorted(arts, key=lambda x: x.get("date",""), reverse=True)
    index_md = f"# {cfg.get('site_name','Site')}\n\n{cfg.get('tagline','')}\n\n---\n\n"
    if arts_sorted:
        index_md += "\n".join(
            f'## <a href="{a["slug"]}.html">{html.escape(a["title"])}</a>\n\n{html.escape(a["desc"])}\n'
            for a in arts_sorted
        )
    else:
        index_md += "Nenhum artigo ainda. Volte em breve!\n"
    index_html = md_to_html(index_md)
    # fix links in index that were escaped
    # md_to_html escapes <a> in headers, so we need to unescape the index title links manually
    # simpler: build index HTML directly
    index_body = f'<h1>{html.escape(cfg.get("site_name","Site"))}</h1><p style="color:#555;font-size:18px">{html.escape(cfg.get("tagline",""))}</p><hr>'
    for a in arts_sorted:
        index_body += f'<p><a href="{a["slug"]}.html"><strong>{html.escape(a["title"])}</strong></a><br><span style="color:#666">{html.escape(a["desc"])}</span><br><small style="color:#999">{html.escape(a["date"])}</small></p>\n'
    if not arts_sorted:
        index_body += "<p>Nenhum artigo ainda. Volte em breve!</p>"

    open(os.path.join(PUBLIC, "index.html"), "w", encoding="utf-8").write(render(cfg.get("site_name", "Site"), index_body, cfg, cfg.get("tagline","")))

    # sitemap
    urls = "\n".join(f"  <url><loc>{site}/{a['slug']}.html</loc><lastmod>{a['date'] or datetime.date.today().isoformat()}</lastmod></url>" for a in arts)
    open(os.path.join(PUBLIC, "sitemap.xml"), "w", encoding="utf-8").write(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url><loc>{site}/</loc><lastmod>{datetime.date.today().isoformat()}</lastmod></url>\n{urls}\n</urlset>')

    # feed.xml (RSS 2.0)
    items = ""
    for a in arts_sorted[:20]:
        items += f"""  <item>
    <title>{html.escape(a['title'])}</title>
    <link>{site}/{a['slug']}.html</link>
    <guid>{site}/{a['slug']}.html</guid>
    <description>{html.escape(a['desc'])}</description>
    <pubDate>{a['date']}</pubDate>
  </item>
"""
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>{html.escape(cfg.get('site_name','Site'))}</title>
  <link>{site}/</link>
  <description>{html.escape(cfg.get('tagline',''))}</description>
  <language>pt-BR</language>
  <lastBuildDate>{datetime.datetime.utcnow().isoformat()}Z</lastBuildDate>
{items}</channel></rss>"""
    open(os.path.join(PUBLIC, "feed.xml"), "w", encoding="utf-8").write(rss)

    # disclosure
    disc_body = """<h1>Política de Afiliados e Divulgação</h1>
<p>Este site participa do Programa de Associados da Amazon e pode incluir links para produtos na Amazon.com.br e Amazon.com.</p>
<p>Quando você clica em um link como <code>{{AMAZON:Exemplo}}</code> e faz uma compra, posso receber uma pequena comissão sem custo adicional para você. Isso ajuda a manter o site no ar e a produzir guias originais e gratuitos.</p>
<p><strong>Transparência:</strong> Todas as recomendações são baseadas em pesquisa prática, testes e análise de ferramentas reais. Não recebo pagamento para ranquear produtos de forma enviesada. Se um produto é ruim, eu digo.</p>
<p>Em conformidade com as diretrizes da Amazon Associates, informo que sou participante do programa e que links de afiliado estão identificados no rodapé de cada artigo.</p>
<p>Dúvidas? Entre em contato pela página inicial.</p>"""
    open(os.path.join(PUBLIC, "disclosure.html"), "w", encoding="utf-8").write(render("Divulgação de Afiliados", disc_body, cfg, "Política de afiliados"))

    print("DONE:", len(arts), "articles ->", PUBLIC)


if __name__ == "__main__":
    main()
