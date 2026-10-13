#!/usr/bin/env python3
"""AutomateIQ static site builder v2. Reads content/*.md -> builds a full static site into ./dist."""
import os, re, shutil, html
from datetime import date
import yaml
import markdown

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
DIST = os.path.join(ROOT, "dist")
SITE_URL = os.environ.get("SITE_URL", "https://automateiq.surge.sh").rstrip("/")
TODAY = date.today().isoformat()
CONTACT_EMAIL = "hello@automateiq.blog"

GOLD = "#d4af37"
GOLD_LT = "#f6df9a"

def _art(inner):
    return (f'<svg class="motif" viewBox="0 0 120 120" fill="none" stroke="{GOLD}" '
            f'stroke-width="4" stroke-linecap="round" stroke-linejoin="round" '
            f'role="img" aria-hidden="true">{inner}</svg>')

# Distinctive hand-crafted SVG motif per article (gold line icons on navy card art)
ARTICLE_ART = {
    # lightning bolt + envelope: instant follow-up
    "ai-lead-follow-up-automation-guide": _art(
        '<rect x="22" y="58" width="76" height="46" rx="8"/>'
        '<path d="M24 64l36 24 36-24"/>'
        '<path d="M66 8L44 52h16l-6 22 26-44H64l8-22z" fill="rgba(212,175,55,.25)"/>'),
    # balance scale: honest comparison
    "n8n-vs-zapier-vs-make-comparison": _art(
        '<path d="M60 18v72M38 90h44"/>'
        '<path d="M60 26L30 34l-9 24a16 16 0 0 0 30 0l-9-24"/>'
        '<path d="M60 26l30 8 9 24a16 16 0 0 1-30 0l9-24"/>'
        f'<circle cx="60" cy="14" r="5" fill="{GOLD}"/>'),
    # warning triangle + cracks: mistakes
    "lead-follow-up-mistakes": _art(
        '<path d="M60 16L14 96h92L60 16z"/>'
        '<path d="M60 44v22"/>'
        f'<circle cx="60" cy="80" r="4" fill="{GOLD}" stroke="none"/>'
        '<path d="M30 108l6-6M90 108l-6-6" stroke-width="3"/>'),
    # gauge dial: lead scoring
    "lead-scoring-explained": _art(
        '<path d="M20 84a40 40 0 0 1 80 0"/>'
        '<path d="M60 84L86 52"/>'
        f'<circle cx="60" cy="84" r="6" fill="{GOLD}" stroke="none"/>'
        '<path d="M28 84h8M84 84h8" stroke-width="3"/>'),
    # circular refresh + spark: revival
    "dead-lead-revival-automation": _art(
        '<path d="M96 60a36 36 0 1 1-10-25"/>'
        '<path d="M96 22v18H78"/>'
        f'<path d="M60 44l-6 14h8l-4 14 14-18h-8l6-10z" fill="{GOLD}" stroke="none"/>'),
    # database cylinder + sparkles: CRM hygiene
    "crm-hygiene-automation": _art(
        '<ellipse cx="52" cy="34" rx="28" ry="10"/>'
        '<path d="M24 34v52c0 6 12 10 28 10s28-4 28-10V34"/>'
        '<path d="M24 60c0 6 12 10 28 10s28-4 28-10"/>'
        f'<path d="M92 22l2 6 6 2-6 2-2 6-2-6-6-2 6-2z" fill="{GOLD_LT}" stroke="none"/>'
        f'<path d="M98 52l1.5 4.5L104 58l-4.5 1.5L98 64l-1.5-4.5L92 58l4.5-1.5z" fill="{GOLD_LT}" stroke="none"/>'),
    # chat bubble vs gear: chatbots vs workflows
    "ai-chatbots-vs-workflow-automation": _art(
        '<path d="M20 30h44v30H44l-12 12v-12H20z"/>'
        '<path d="M32 42h20M32 50h14" stroke-width="3"/>'
        f'<circle cx="88" cy="82" r="14"/>'
        f'<circle cx="88" cy="82" r="5" fill="{GOLD}" stroke="none"/>'
        '<path d="M88 62v6M88 96v6M68 82h6M102 82h6M74 68l4 4M98 92l4 4M102 68l-4 4M74 92l-4 4" stroke-width="3"/>'),
    # bar chart + trend arrow: weekly reports
    "automated-weekly-sales-reports-n8n": _art(
        '<path d="M24 104h72"/>'
        '<rect x="30" y="66" width="14" height="38" rx="3"/>'
        '<rect x="52" y="52" width="14" height="52" rx="3"/>'
        '<rect x="74" y="38" width="14" height="66" rx="3"/>'
        '<path d="M28 60l26-18 16 10 24-22"/>'
        '<path d="M86 30h10v10"/>'),
    # paper plane: outreach templates
    "outreach-message-templates": _art(
        '<path d="M104 20L56 68l14 6 6 14 48-48z"/>'
        '<path d="M104 20L56 68"/>'
        '<path d="M16 96l24-6-4 10"/>'
        f'<circle cx="30" cy="30" r="4" fill="{GOLD_LT}" stroke="none"/>'
        f'<circle cx="92" cy="96" r="4" fill="{GOLD_LT}" stroke="none"/>'),
    # rocket: productize services
    "productize-automation-services-agencies": _art(
        '<path d="M60 12c14 10 18 28 12 44l-12 14-12-14c-6-16-2-34 12-44z"/>'
        '<circle cx="60" cy="38" r="7"/>'
        '<path d="M48 56L34 78l12-4M72 56l14 22-12-4"/>'
        '<path d="M54 82c0 8-4 12-10 14M66 82c0 8 4 12 10 14"/>'
        f'<circle cx="94" cy="30" r="4" fill="{GOLD_LT}" stroke="none"/>'),
}

# fallback per-category icon (kept for any future uncategorized article)
CATEGORY_ICONS = {
    "Guides": _art('<path d="M34 26h52v68H34z"/><path d="M34 26l26 20 26-20"/><path d="M46 60h28M46 72h18" stroke-width="3"/>'),
    "Comparisons": _art('<path d="M46 20v80M74 20v80"/><path d="M28 44h18M28 76h18M74 44h18M74 76h18"/>'),
    "Strategy": _art('<circle cx="60" cy="60" r="34"/><circle cx="60" cy="60" r="17"/><circle cx="60" cy="60" r="4" fill="' + GOLD + '" stroke="none"/>'),
    "Tutorials": _art('<path d="M40 84l28-28-28-28"/><path d="M66 92h28" />'),
}

def art_for(a):
    return ARTICLE_ART.get(a["slug"], CATEGORY_ICONS.get(a["category"], CATEGORY_ICONS["Guides"]))

def esc(s): return html.escape(s or "", quote=True)

def parse_frontmatter(text):
    try:
        return yaml.safe_load(text)
    except Exception:
        meta = {}
        for line in text.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"').strip("'")
        return meta

def enhance_html(body_html):
    """Convert **Tip:/**Note:/**Warning:/**Important: lead paragraphs into styled callouts."""
    def repl(m):
        kind = m.group(1).lower()
        label = m.group(1)
        rest = m.group(2)
        return (f'<div class="callout callout-{kind}"><strong>{label}</strong>'
                f'<p style="margin:0">{rest}</p></div>')
    return re.sub(r"<p><strong>(Tip|Note|Warning|Important):</strong>\s*(.*?)</p>",
                  repl, body_html, flags=re.S)

def load_articles():
    arts = []
    for fn in sorted(os.listdir(CONTENT)):
        if not fn.endswith(".md"):
            continue
        raw = open(os.path.join(CONTENT, fn), encoding="utf-8").read()
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
        if not m:
            raise ValueError(f"No frontmatter in {fn}")
        meta = parse_frontmatter(m.group(1))
        body_md = m.group(2)
        body_html = markdown.markdown(body_md, extensions=["extra"])
        body_html = re.sub(r"^<h1>.*?</h1>\s*", "", body_html, count=1, flags=re.S)
        body_html = enhance_html(body_html)
        body_html = insert_inarticle_ad(body_html)
        words = len(re.findall(r"\w+", body_md))
        arts.append({
            "slug": meta["slug"], "title": meta["title"], "description": meta["description"],
            "date": str(meta.get("date", TODAY)), "category": meta.get("category", "Guides"),
            "html": body_html, "words": words,
        })
    arts.sort(key=lambda a: a["date"], reverse=True)
    return arts

def insert_inarticle_ad(body_html):
    ad = '<div class="ad-slot ad-inarticle">Advertisement<!-- Google AdSense in-article unit goes here --></div>'
    parts = re.split(r"(<h2[^>]*>)", body_html)
    if len(parts) >= 5:
        out = []
        count = 0
        for p in parts:
            out.append(p)
            if p.startswith("<h2"):
                count += 1
                if count == 2:
                    out.append(ad)
        return "".join(out)
    mid = len(body_html) // 2
    cut = body_html.find("</p>", mid)
    if cut == -1: cut = mid
    else: cut += 4
    return body_html[:cut] + ad + body_html[cut:]

FAVICON_URI = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
               "%3Crect width='64' height='64' rx='14' fill='%230a1628'/%3E"
               "%3Ctext x='32' y='44' font-family='Georgia,serif' font-size='36' font-weight='bold' "
               "fill='%23d4af37' text-anchor='middle'%3EA%3C/text%3E%3C/svg%3E")

def head(title, description, path, og_type="website"):
    url = SITE_URL + path
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | AutomateIQ</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(url)}">
<meta property="og:site_name" content="AutomateIQ">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(url)}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700;9..144,900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/main.css">
<link rel="icon" href="{FAVICON_URI}" type="image/svg+xml">"""

def header(active):
    def link(href, label, key):
        cls = ' class="active"' if active == key else ""
        return f'<a href="{href}"{cls}>{label}</a>'
    return f"""<header class="site-header" id="siteHeader">
  <div class="header-inner">
    <a class="brand" href="/" aria-label="AutomateIQ home">
      <span class="brand-mark">A</span>
      <span><span class="brand-name">Automate<em>IQ</em></span>
      <span class="brand-tag">AI automation playbooks</span></span>
    </a>
    <button class="nav-toggle" aria-label="Menu" aria-expanded="false">&#9776;</button>
    <nav class="main-nav" id="mainNav" aria-label="Main navigation">
      {link("/", "Home", "home")}
      {link("/articles/", "Articles", "articles")}
      {link("/about.html", "About", "about")}
      {link("/contact.html", "Contact", "contact")}
    </nav>
  </div>
</header>"""

def footer(recent):
    recent_links = "".join(
        f'<li><a href="/articles/{a["slug"]}.html">{esc(a["title"][:52])}{"…" if len(a["title"]) > 52 else ""}</a></li>'
        for a in recent[:4]
    )
    return f"""<footer class="site-footer">
  <div class="footer-grid">
    <div>
      <h4>Automate<em style="color:var(--gold-400);font-style:normal">IQ</em></h4>
      <p style="font-size:15px">AI automation playbooks for growing businesses. Practical guides on lead follow-up, n8n workflows, CRM automation, and outreach that actually works.</p>
    </div>
    <div>
      <h4>Explore</h4>
      <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/articles/">All articles</a></li>
        <li><a href="/about.html">About</a></li>
        <li><a href="/contact.html">Contact</a></li>
      </ul>
    </div>
    <div>
      <h4>Topics</h4>
      <ul>
        <li><a href="/articles/#cat-Guides">Guides</a></li>
        <li><a href="/articles/#cat-Comparisons">Comparisons</a></li>
        <li><a href="/articles/#cat-Strategy">Strategy</a></li>
        <li><a href="/articles/#cat-Tutorials">Tutorials</a></li>
      </ul>
    </div>
    <div>
      <h4>Latest</h4>
      <ul>{recent_links}</ul>
    </div>
    <div>
      <h4>Legal</h4>
      <ul>
        <li><a href="/privacy.html">Privacy Policy</a></li>
        <li><a href="/terms.html">Terms of Service</a></li>
      </ul>
    </div>
  </div>
  <div class="footer-bottom">&copy; <span id="year">2026</span> AutomateIQ. All rights reserved. Content is for educational purposes only.</div>
</footer>
<script src="/assets/js/main.js"></script>"""

def page(title, description, path, body, active="", og_type="website", recent=()):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head(title, description, path, og_type)}
</head>
<body>
{header(active)}
{body}
{footer(recent)}
</body>
</html>"""

def card(a):
    return f"""<article class="card reveal" data-cat="{esc(a["category"])}">
  <div class="card-art">{art_for(a)}</div>
  <div class="card-body">
    <div class="card-cat">{esc(a["category"])}</div>
    <h3><a href="/articles/{a["slug"]}.html">{esc(a["title"])}</a></h3>
    <p>{esc(a["description"])}</p>
    <div class="card-meta"><time datetime="{a["date"]}">{a["date"]}</time> &middot; {a["words"]:,} words</div>
  </div>
</article>"""

def related_articles(a, articles, n=3):
    same = [x for x in articles if x["slug"] != a["slug"] and x["category"] == a["category"]]
    others = [x for x in articles if x["slug"] != a["slug"] and x["category"] != a["category"]]
    picks = (same + others)[:n]
    cards_html = "".join(card(p) for p in picks)
    return f"""<section class="related">
  <h2>Keep reading</h2>
  <div class="cards">{cards_html}</div>
</section>"""

def article_page(a, articles):
    recent_items = "".join(
        f'<li><a href="/articles/{r["slug"]}.html">{esc(r["title"])}</a></li>'
        for r in articles if r["slug"] != a["slug"]
    )[:5]
    body = f"""<div class="read-progress" aria-hidden="true"><span id="readBar"></span></div>
<div class="article-hero">
  <div class="wrap">
    <p class="kicker">{esc(a["category"])}</p>
    <h1>{esc(a["title"])}</h1>
    <p class="lede">{esc(a["description"])}</p>
    <div class="article-meta">By <strong style="color:#e8e2d0">AutomateIQ Editorial Team</strong> &middot; <time datetime="{a["date"]}">{a["date"]}</time> &middot; {a["words"]:,} words</div>
  </div>
</div>
<div class="ad-slot ad-leaderboard">Advertisement<!-- Google AdSense display unit goes here --></div>
<div class="article-layout">
  <article class="prose">
    {a["html"]}
    {related_articles(a, articles)}
  </article>
  <aside class="sidebar" aria-label="Sidebar">
    <div class="ad-slot ad-sidebar">Advertisement<!-- Google AdSense sidebar unit goes here --></div>
    <div class="widget">
      <h4>Latest articles</h4>
      <ul>{recent_items}</ul>
    </div>
    <div class="widget">
      <h4>About AutomateIQ</h4>
      <p style="font-size:15px;margin:0">Practical AI automation playbooks for growing businesses. <a href="/about.html">Learn more &rarr;</a></p>
    </div>
  </aside>
</div>"""
    return page(a["title"], a["description"], f"/articles/{a['slug']}.html", body,
                active="articles", og_type="article", recent=articles)

HERO_BG_SVG = """<svg class="hero-bg" viewBox="0 0 1200 520" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
  <defs>
    <radialGradient id="hglow" cx="50%" cy="0%" r="70%">
      <stop offset="0%" stop-color="#d4af37" stop-opacity=".22"/>
      <stop offset="100%" stop-color="#d4af37" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1200" height="520" fill="url(#hglow)"/>
  <g stroke="#d4af37" stroke-width="1.4" class="flow-line">
    <path d="M180 360 C 320 300, 420 240, 560 250" fill="none"/>
    <path d="M560 250 C 700 260, 800 180, 940 190" fill="none"/>
    <path d="M300 420 C 480 400, 700 380, 900 330" fill="none" opacity=".6"/>
  </g>
  <g class="node">
    <circle cx="180" cy="360" r="26" fill="#10203a" stroke="#d4af37" stroke-width="2.5"/>
    <circle cx="180" cy="360" r="8" fill="#d4af37"/>
  </g>
  <g class="node" style="animation-delay:-2s">
    <rect x="534" y="224" width="52" height="52" rx="12" fill="#10203a" stroke="#d4af37" stroke-width="2.5"/>
    <path d="M548 250h24M560 238v24" stroke="#d4af37" stroke-width="2.5" stroke-linecap="round"/>
  </g>
  <g class="node" style="animation-delay:-4.5s">
    <circle cx="940" cy="190" r="30" fill="#10203a" stroke="#d4af37" stroke-width="2.5"/>
    <path d="M928 190h24M940 178v24" stroke="#d4af37" stroke-width="2.5" stroke-linecap="round"/>
  </g>
  <g class="node" style="animation-delay:-1s">
    <circle cx="1020" cy="330" r="18" fill="#10203a" stroke="#d4af37" stroke-width="2"/>
    <path d="M1012 330l6 6 10-12" stroke="#d4af37" stroke-width="2.5" fill="none" stroke-linecap="round"/>
  </g>
  <g fill="#d4af37">
    <circle class="particle" cx="260" cy="460" r="3.5" style="animation-delay:0s"/>
    <circle class="particle" cx="420" cy="470" r="2.5" style="animation-delay:-3s"/>
    <circle class="particle" cx="620" cy="460" r="4" style="animation-delay:-6s"/>
    <circle class="particle" cx="800" cy="470" r="2.5" style="animation-delay:-1.5s"/>
    <circle class="particle" cx="980" cy="460" r="3.5" style="animation-delay:-7.5s"/>
    <circle class="particle" cx="140" cy="470" r="2.5" style="animation-delay:-4.5s"/>
    <circle class="particle" cx="520" cy="480" r="3" style="animation-delay:-2.2s"/>
    <circle class="particle" cx="720" cy="480" r="2" style="animation-delay:-8.4s"/>
  </g>
</svg>"""

ABOUT_BODY = """<div class="page-hero"><div class="wrap"><h1>About AutomateIQ</h1></div></div>
<div class="page-body">
<p><strong>AutomateIQ</strong> is an independent publication about AI automation for growing businesses. We write practical playbooks on lead follow-up automation, n8n workflows, CRM hygiene, lead scoring, and outreach — the unglamorous systems that actually move revenue.</p>
<h2>What we cover</h2>
<ul>
<li>Lead capture, follow-up, and revival automation</li>
<li>Honest tool comparisons (n8n, Zapier, Make, CRMs)</li>
<li>Step-by-step tutorials a non-developer can follow</li>
<li>Outreach and sales process strategy</li>
</ul>
<h2>Editorial standards</h2>
<ul>
<li><strong>Original content.</strong> Every article is written from scratch for this publication.</li>
<li><strong>No hype, no fake proof.</strong> We don't publish fabricated case studies, invented statistics, or income claims. When we share an estimate, we label it as one.</li>
<li><strong>Tools over theory.</strong> If we recommend a tool, we explain exactly what it does and where it falls short.</li>
</ul>
<h2>Who writes this</h2>
<p>Articles are written by the <strong>AutomateIQ Editorial Team</strong> — operators and builders who work with automation daily. Have a topic suggestion or a correction? <a href="/contact.html">Contact us</a>.</p>
<h2>Disclosure</h2>
<p>AutomateIQ may earn revenue from advertising (such as Google AdSense) and affiliate links in the future. Any affiliate relationship will be clearly disclosed in the article where it appears.</p>
</div>"""

CONTACT_BODY = f"""<div class="page-hero"><div class="wrap"><h1>Contact</h1></div></div>
<div class="page-body">
<p>Questions, topic suggestions, corrections, or business inquiries — we'd love to hear from you. Fill in the form and it will open your email app with everything pre-filled.</p>
<form class="contact-form" id="contactForm">
  <label for="cf-name">Name</label>
  <input id="cf-name" name="name" type="text" required autocomplete="name">
  <label for="cf-email">Email</label>
  <input id="cf-email" name="email" type="email" required autocomplete="email">
  <label for="cf-topic">Topic</label>
  <select id="cf-topic" name="topic">
    <option>Article suggestion</option>
    <option>Correction</option>
    <option>Business inquiry</option>
    <option>Other</option>
  </select>
  <label for="cf-message">Message</label>
  <textarea id="cf-message" name="message" required></textarea>
  <p style="margin-top:20px"><button class="btn" type="submit">Send via email</button></p>
  <p class="form-note" id="formNote">This form opens your own email client — nothing is sent automatically, and we never see your message unless you press send in your email app. You can also email us directly at {CONTACT_EMAIL}.</p>
</form>
</div>"""

PRIVACY_BODY = f"""<div class="page-hero"><div class="wrap"><h1>Privacy Policy</h1></div></div>
<div class="page-body">
<p><em>Last updated: {TODAY}</em></p>
<p>AutomateIQ ("we", "us") respects your privacy. This policy explains what information we collect and how it is used.</p>
<h2>Information we collect</h2>
<p>This website does not require accounts and does not collect personal information directly. If you contact us by email, we receive your name, email address, and message solely to respond to your inquiry.</p>
<h2>Cookies and advertising</h2>
<p>We may display ads served by Google AdSense or similar providers. Third-party vendors, including Google, use cookies to serve ads based on your prior visits to this and other websites. Google's use of advertising cookies enables it and its partners to serve ads based on your visit to our site.</p>
<p>You may opt out of personalized advertising by visiting <a href="https://www.google.com/settings/ads" rel="noopener">Google Ads Settings</a>. Alternatively, you can opt out of some third-party vendors' use of cookies for personalized advertising at <a href="https://www.aboutads.info/choices/" rel="noopener">aboutads.info/choices</a>.</p>
<h2>Analytics</h2>
<p>We may use privacy-respecting analytics to understand aggregate readership (pages viewed, approximate geography). This data is never sold.</p>
<h2>Data retention and your rights</h2>
<p>Emails you send us are kept only as long as needed to handle your request. You may ask us to delete your correspondence at any time by emailing {CONTACT_EMAIL}.</p>
<h2>Children</h2>
<p>This site is not directed at children under 13, and we do not knowingly collect their information.</p>
<h2>Changes</h2>
<p>We may update this policy; the "last updated" date above will reflect changes.</p>
<h2>Contact</h2>
<p>Questions about this policy: {CONTACT_EMAIL}.</p>
</div>"""

TERMS_BODY = f"""<div class="page-hero"><div class="wrap"><h1>Terms of Service</h1></div></div>
<div class="page-body">
<p><em>Last updated: {TODAY}</em></p>
<h2>Acceptance</h2>
<p>By accessing AutomateIQ, you agree to these terms. If you do not agree, please do not use the site.</p>
<h2>Educational content only</h2>
<p>All articles are published for general educational purposes. They are not professional, financial, legal, or business advice. Automation results vary by business; we make no guarantees of any outcome, revenue, or performance from applying the ideas discussed.</p>
<h2>Intellectual property</h2>
<p>All content on AutomateIQ is original and owned by AutomateIQ unless stated otherwise. You may quote brief excerpts with attribution and a link back. Reproducing full articles without written permission is not allowed.</p>
<h2>Acceptable use</h2>
<p>You agree not to misuse the site, attempt to disrupt it, scrape content at abusive rates, or misrepresent our content as your own.</p>
<h2>Third-party links and tools</h2>
<p>We mention third-party tools and link to external sites for reference. We do not control those sites and are not responsible for their content, accuracy, or practices.</p>
<h2>Limitation of liability</h2>
<p>To the maximum extent permitted by law, AutomateIQ is not liable for any damages arising from your use of, or reliance on, this site's content.</p>
<h2>Changes</h2>
<p>We may revise these terms; continued use of the site constitutes acceptance of the updated terms.</p>
<h2>Contact</h2>
<p>{CONTACT_EMAIL}</p>
</div>"""

NOTFOUND_BODY = """<div class="page-hero"><div class="wrap"><h1>Page not found</h1></div></div>
<div class="page-body" style="text-align:center">
<p>The page you're looking for doesn't exist or has moved.</p>
<p><a class="btn" href="/">Back to home</a></p>
</div>"""

def featured_band(a):
    return f"""<section class="spotlight">
  <div class="wrap spotlight-grid">
    <div class="spotlight-art reveal">{art_for(a)}</div>
    <div class="reveal">
      <p class="kicker" style="color:var(--gold-300)">Featured playbook</p>
      <h2>{esc(a["title"])} — <span class="grad">the complete starter system</span></h2>
      <p>{esc(a["description"])}</p>
      <p><a class="btn" href="/articles/{a["slug"]}.html">Read the playbook</a></p>
    </div>
  </div>
</section>"""

def build():
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(os.path.join(DIST, "articles"))
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(DIST, "assets"))

    articles = load_articles()
    print(f"Loaded {len(articles)} articles")
    by_slug = {a["slug"]: a for a in articles}
    featured = by_slug.get("ai-lead-follow-up-automation-guide", articles[0])

    # Article pages
    for a in articles:
        out = os.path.join(DIST, "articles", a["slug"] + ".html")
        open(out, "w", encoding="utf-8").write(article_page(a, articles))

    # Home
    latest = [a for a in articles if a["slug"] != featured["slug"]][:6]
    cards_html = "".join(card(a) for a in latest)
    home_body = f"""<section class="hero">
  {HERO_BG_SVG}
  <div class="hero-inner">
    <p class="kicker">Practical AI automation &middot; No hype</p>
    <h1>Turn lost leads into <span class="grad">revenue machines</span></h1>
    <p class="sub">Step-by-step playbooks on AI follow-up, n8n workflows, lead scoring, and outreach systems — written for business owners, not engineers.</p>
    <div class="hero-ctas">
      <a class="btn" href="/articles/">Start reading</a>
      <a class="btn btn-ghost" href="/about.html">What we do</a>
    </div>
    <div class="hero-stats">
      <div><b>10</b><span>In-depth guides</span></div>
      <div><b>4</b><span>Topic areas</span></div>
      <div><b>100%</b><span>Original content</span></div>
    </div>
  </div>
</section>
<div class="ad-slot ad-leaderboard">Advertisement<!-- Google AdSense display unit goes here --></div>
{featured_band(featured)}
<section class="section"><div class="wrap">
  <div class="section-head"><h2>Latest articles</h2><a href="/articles/">View all &rarr;</a></div>
  <div class="cards">{cards_html}</div>
</div></section>"""
    open(os.path.join(DIST, "index.html"), "w", encoding="utf-8").write(
        page("AI Automation Playbooks for Growing Businesses",
             "AutomateIQ: practical, hype-free guides on AI lead follow-up, n8n workflows, CRM automation, lead scoring, and outreach for small businesses and agencies.",
             "/", home_body, active="home", recent=articles))

    # Articles index with topic filter
    cats = sorted({a["category"] for a in articles})
    filter_btns = '<button class="filter-btn on" data-filter="all">All</button>' + "".join(
        f'<button class="filter-btn" data-filter="{esc(c)}">{esc(c)}</button>' for c in cats)
    all_cards = "".join(card(a) for a in articles)
    idx_body = f"""<div class="page-hero"><div class="wrap"><h1>All articles</h1></div></div>
<div class="ad-slot ad-leaderboard">Advertisement<!-- Google AdSense display unit goes here --></div>
<section class="section" style="padding-top:24px"><div class="wrap">
  <div class="filter-bar" role="group" aria-label="Filter by topic">{filter_btns}</div>
  <div class="cards" id="articleGrid">{all_cards}</div>
</div></section>"""
    open(os.path.join(DIST, "articles", "index.html"), "w", encoding="utf-8").write(
        page("All Articles", "Browse every AutomateIQ guide on AI automation, lead follow-up, n8n tutorials, CRM hygiene, and outreach strategy.",
             "/articles/", idx_body, active="articles", recent=articles))

    # Static pages
    for name, title, desc, path, body, active in [
        ("about.html", "About", "About AutomateIQ: independent publication on AI automation playbooks for growing businesses.", "/about.html", ABOUT_BODY, "about"),
        ("contact.html", "Contact", "Contact the AutomateIQ editorial team.", "/contact.html", CONTACT_BODY, "contact"),
        ("privacy.html", "Privacy Policy", "AutomateIQ privacy policy.", "/privacy.html", PRIVACY_BODY, ""),
        ("terms.html", "Terms of Service", "AutomateIQ terms of service.", "/terms.html", TERMS_BODY, ""),
        ("404.html", "Page not found", "Page not found.", "/404.html", NOTFOUND_BODY, ""),
    ]:
        open(os.path.join(DIST, name), "w", encoding="utf-8").write(
            page(title, desc, path, body, active=active, recent=articles))

    # robots.txt + sitemap.xml
    open(os.path.join(DIST, "robots.txt"), "w").write(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    urls = ["/", "/articles/", "/about.html", "/contact.html", "/privacy.html", "/terms.html"]
    urls += [f"/articles/{a['slug']}.html" for a in articles]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append(f"  <url><loc>{SITE_URL}{u}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq></url>")
    sm.append("</urlset>")
    open(os.path.join(DIST, "sitemap.xml"), "w").write("\n".join(sm))

    total = sum(1 for _, _, fs in os.walk(DIST) for f in fs)
    print(f"Built {total} files into {DIST}")
    return articles

if __name__ == "__main__":
    arts = build()
    for a in arts:
        print(f"  - {a['slug']}: {a['words']:,} words")
