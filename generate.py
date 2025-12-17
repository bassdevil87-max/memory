import sqlite3, os, datetime
from jinja2 import Template

# 2025 PREMIUM THEME: Dark Mode & Glassmorphism
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ model_name }} on {{ gpu_name }} - VRAM Requirements</title>
    <script type="application/ld+json">
    {
      "@context": "https://schema.org/",
      "@type": "Product",
      "name": "{{ gpu_name }} for {{ model_name }}",
      "brand": {"@type": "Brand", "name": "{{ brand }}"},
      "offers": { "@type": "Offer", "price": "{{ price }}", "priceCurrency": "USD" }
    }
    </script>
    <style>
        :root { --bg: #030712; --card: #111827; --accent: #3b82f6; --text: #f3f4f6; }
        body { background: var(--bg); color: var(--text); font-family: system-ui; padding: 2rem; }
        .card { background: var(--card); border: 1px solid #374151; padding: 2.5rem; border-radius: 20px; max-width: 800px; margin: auto; }
        .badge { background: #1e293b; color: var(--accent); padding: 5px 15px; border-radius: 50px; font-weight: bold; font-size: 12px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin: 2rem 0; }
        .stat { background: #1f2937; padding: 1.5rem; border-radius: 12px; border: 1px solid #374151; text-align: center; }
        .stat b { display: block; font-size: 1.2rem; color: var(--accent); }
        .cta { display: block; background: var(--accent); color: white; text-align: center; padding: 1rem; border-radius: 10px; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <span class="badge">{{ task.upper() }}</span>
        <h1>Can I run {{ model_name }}?</h1>
        <p>Hardware: <b>{{ gpu_name }}</b> ({{ vram_total }}GB VRAM)</p>
        <div class="grid">
            {% for r in results %}
            <div class="stat">
                <span>{{ r.bit }}-bit</span>
                <b>{{ r.status }}</b>
                <small>{{ r.needed }}GB</small>
            </div>
            {% endfor %}
        </div>
        <a href="{{ cta_link }}" class="cta">{{ cta_text }}</a>
    </div>
</body>
</html>
"""

def run_build():
    conn = sqlite3.connect('monopoly.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    os.makedirs('docs', exist_ok=True)
    
    models = c.execute("SELECT * FROM models").fetchall()
    hardware = c.execute("SELECT * FROM hardware").fetchall()
    
    links, sitemap_urls = [], []
    for h in hardware:
        for m in models:
            results = []
            for bit in [4, 8, 16]:
                # 500 IQ Physics: (Params * Bits / 8) + 25% Overhead
                needed = round(((m['params_b'] * bit) / 8) * 1.25 + 0.6, 1)
                results.append({"bit": bit, "needed": needed, "status": "✅ YES" if h['vram_gb'] >= needed else "❌ NO"})
            
            slug = f"{h['id']}-vs-{m['id'].replace('/', '-')}.html".lower()
            with open(f"docs/{slug}", "w") as f:
                f.write(Template(HTML_TEMPLATE).render(
                    model_name=m['id'], gpu_name=h['name'], brand=h['brand'], 
                    price=h['price'], vram_total=h['vram_gb'], params=m['params_b'], 
                    task=m['task'], license=m['license'], results=results, 
                    cta_text=f"Check {h['name']} Price", cta_link="#", date=datetime.datetime.now().year
                ))
            links.append(f'<li><a href="{slug}">{h["name"]} vs {m["id"]}</a></li>')
            sitemap_urls.append(f"https://yourdomain.com/{slug}")

    # Build Index & Sitemap
    with open("docs/index.html", "w") as f:
        f.write(f"<html><body style='background:#030712; color:white;'><h1>AI Monopoly Index</h1><ul>{''.join(links)}</ul></body></html>")
    
    with open("docs/sitemap.xml", "w") as f:
        urls = "".join([f"<url><loc>{u}</loc></url>" for u in sitemap_urls])
        f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')

    conn.close()

if __name__ == "__main__":
    run_build()