import sqlite3, os, datetime
from jinja2 import Template

# 2025 PREMIUM THEME: Glassmorphism & Cyber-Blue
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ model_name }} on {{ gpu_name }} - VRAM Requirements</title>
    <style>
        :root { --bg: #020617; --card: rgba(30, 41, 59, 0.7); --accent: #3b82f6; --text: #f8fafc; --success: #22c55e; --fail: #ef4444; }
        body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; padding: 2rem; margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .container { background: var(--card); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1); padding: 3rem; border-radius: 24px; max-width: 900px; width: 100%; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); }
        .badge { background: rgba(59, 130, 246, 0.2); color: var(--accent); padding: 6px 16px; border-radius: 99px; font-weight: 700; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }
        h1 { font-size: 2.5rem; margin: 1rem 0; font-weight: 800; }
        .subtitle { color: #94a3b8; font-size: 1.1rem; margin-bottom: 2rem; }
        .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 2.5rem 0; }
        .stat-card { background: rgba(15, 23, 42, 0.5); padding: 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05); transition: 0.3s; }
        .stat-card:hover { transform: translateY(-5px); border-color: var(--accent); }
        .stat-card span { display: block; color: #94a3b8; font-size: 0.9rem; margin-bottom: 0.5rem; }
        .stat-card b { font-size: 1.5rem; color: var(--text); }
        .status-pill { display: inline-block; padding: 4px 12px; border-radius: 6px; font-weight: bold; margin-top: 10px; }
        .yes { background: rgba(34, 197, 94, 0.1); color: var(--success); }
        .no { background: rgba(239, 68, 68, 0.1); color: var(--fail); }
        .cta-btn { display: block; background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; text-align: center; padding: 1.2rem; border-radius: 12px; text-decoration: none; font-weight: 700; font-size: 1.1rem; transition: 0.3s; box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.4); }
        .cta-btn:hover { transform: scale(1.02); filter: brightness(1.1); }
    </style>
</head>
<body>
    <div class="container">
        <span class="badge">{{ task.upper() }} Compatibility</span>
        <h1>Can you run {{ model_name }}?</h1>
        <p class="subtitle">Detailed analysis for <b>{{ gpu_name }}</b> ({{ vram_total }}GB VRAM)</p>
        
        <div class="grid">
            {% for r in results %}
            <div class="stat-card">
                <span>{{ r.bit }}-bit Quantization</span>
                <b>{{ r.needed }} GB</b>
                <div class="status-pill {{ 'yes' if 'YES' in r.status else 'no' }}">{{ r.status }}</div>
            </div>
            {% endfor %}
        </div>
        
        <a href="{{ cta_link }}" class="cta-btn">{{ cta_text }}</a>
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
    base_url = "https://bassdevil87-max.github.io/memory"

    for h in hardware:
        for m in models:
            results = []
            for bit in [4, 8, 16]:
                # Overhead calculation
                needed = round(((m['params_b'] * bit) / 8) * 1.25 + 0.6, 1)
                results.append({"bit": bit, "needed": needed, "status": "✅ YES" if h['vram_gb'] >= needed else "❌ NO"})
            
            slug = f"{h['id']}-vs-{m['id'].replace('/', '-')}.html".lower()
            with open(f"docs/{slug}", "w") as f:
                f.write(Template(HTML_TEMPLATE).render(
                    model_name=m['id'], gpu_name=h['name'], brand=h['brand'], 
                    price=h['price'], vram_total=h['vram_gb'], params=m['params_b'], 
                    task=m['task'], results=results, 
                    cta_text=f"Check {h['name']} Current Price", cta_link="https://amazon.com", date=2025
                ))
            links.append(f'<li><a href="{slug}">{h["name"]} vs {m["id"]}</a></li>')
            sitemap_urls.append(f"{base_url}/{slug}")

    # PRETTIER INDEX PAGE
    index_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>VRAM.wiki | AI Hardware Monopoly</title>
        <style>
            body {{ background: #020617; color: white; font-family: 'Inter', sans-serif; padding: 5vw; }}
            h1 {{ font-size: 3rem; background: linear-gradient(to right, #3b82f6, #93c5fd); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
            .search-box {{ width: 100%; padding: 1rem; border-radius: 12px; border: 1px solid #1e293b; background: #0f172a; color: white; margin: 2rem 0; font-size: 1.2rem; }}
            ul {{ list-style: none; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 15px; }}
            li a {{ display: block; background: #1e293b; padding: 1.5rem; border-radius: 12px; text-decoration: none; color: #cbd5e1; border: 1px solid transparent; transition: 0.3s; }}
            li a:hover {{ border-color: #3b82f6; background: #26334d; color: white; transform: scale(1.02); }}
        </style>
    </head>
    <body>
        <h1>VRAM.wiki</h1>
        <p>The Global Database for AI Model Hardware Compatibility.</p>
        <input type="text" class="search-box" placeholder="Search for a model (e.g. Llama 3)..." id="search">
        <ul id="list">{''.join(links)}</ul>
        <script>
            document.getElementById('search').onkeyup = function() {{
                let val = this.value.toLowerCase();
                document.querySelectorAll('#list li').forEach(li => {{
                    li.style.display = li.textContent.toLowerCase().includes(val) ? '' : 'none';
                }});
            }};
        </script>
    </body>
    </html>
    """
    with open("docs/index.html", "w") as f:
        f.write(index_html)
    
    # (Sitemap logic remains the same)
    sitemap_xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{base_url}/index.html</loc></url>{"".join([f"<url><loc>{u}</loc></url>" for u in sitemap_urls])}</urlset>'
    with open("docs/sitemap.xml", "w") as f:
        f.write(sitemap_xml)
    conn.close()

if __name__ == "__main__":
    run_build()