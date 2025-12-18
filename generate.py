import sqlite3, os, datetime
from jinja2 import Template

# --- PREMIUM PAGE TEMPLATE (Individual Comparisons) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ model_name }} on {{ gpu_name }} - VRAM.wiki</title>
    <style>
        :root { --bg: #020617; --card: rgba(30, 41, 59, 0.7); --accent: #3b82f6; --text: #f8fafc; --success: #22c55e; --fail: #ef4444; }
        body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; padding: 2rem; margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .container { background: var(--card); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1); padding: 3rem; border-radius: 24px; max-width: 800px; width: 100%; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); }
        .badge { background: rgba(59, 130, 246, 0.2); color: var(--accent); padding: 6px 16px; border-radius: 99px; font-weight: 700; font-size: 0.8rem; text-transform: uppercase; }
        h1 { font-size: 2.2rem; margin: 1rem 0; font-weight: 800; }
        .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 2rem 0; }
        .stat-card { background: rgba(15, 23, 42, 0.5); padding: 1.2rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05); text-align: center; }
        .stat-card b { display: block; font-size: 1.4rem; color: var(--accent); margin: 5px 0; }
        .status-pill { display: inline-block; padding: 4px 12px; border-radius: 6px; font-weight: bold; margin-top: 10px; font-size: 0.8rem; }
        .yes { background: rgba(34, 197, 94, 0.1); color: var(--success); }
        .no { background: rgba(239, 68, 68, 0.1); color: var(--fail); }
        .cta { display: block; background: #3b82f6; color: white; text-align: center; padding: 1.1rem; border-radius: 12px; text-decoration: none; font-weight: bold; margin-top: 2rem; }
    </style>
</head>
<body>
    <div class="container">
        <span class="badge">{{ task }} Compatibility</span>
        <h1>Can I run {{ model_name }}?</h1>
        <p>Tested on <b>{{ gpu_name }}</b> ({{ vram_total }}GB VRAM)</p>
        <div class="grid">
            {% for r in results %}
            <div class="stat-card">
                <span>{{ r.bit }}-bit</span>
                <b>{{ r.needed }}GB</b>
                <span class="status-pill {{ 'yes' if 'YES' in r.status else 'no' }}">{{ r.status }}</span>
            </div>
            {% endfor %}
        </div>
        <a href="{{ cta_link }}" class="cta">Check {{ gpu_name }} Price</a>
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
            max_needed = 0
            for bit in [4, 8, 16]:
                needed = round(((m['params_b'] * bit) / 8) * 1.25 + 0.6, 1)
                if bit == 4: max_needed = needed # Use 4-bit as our baseline for the filter
                results.append({"bit": bit, "needed": needed, "status": "✅ YES" if h['vram_gb'] >= needed else "❌ NO"})
            
            slug = f"{h['id']}-vs-{m['id'].replace('/', '-')}.html".lower()
            with open(f"docs/{slug}", "w") as f:
                f.write(Template(HTML_TEMPLATE).render(
                    model_name=m['id'], gpu_name=h['name'], vram_total=h['vram_gb'], 
                    task=m['task'], results=results, cta_link="#", date=2025
                ))
            
            # Data-VRAM attribute allows the slider to filter these
            links.append(f'''
                <a href="{slug}" class="card" data-vram="{max_needed}">
                    <span class="gpu-tag">{h['name']}</span>
                    <span class="model-name">{m['id']}</span>
                    <span class="vram-req">Min VRAM: {max_needed}GB</span>
                </a>''')
            sitemap_urls.append(f"{base_url}/{slug}")

    # --- THE INTERACTIVE INDEX ---
    index_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>VRAM.wiki | AI Hardware Wizard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            :root {{ --bg: #020617; --card: #1e293b; --accent: #3b82f6; --text: #f8fafc; }}
            body {{ background: var(--bg); color: var(--text); font-family: system-ui, sans-serif; padding: 2rem; margin: 0; }}
            .hero {{ text-align: center; margin: 4rem auto 2rem; max-width: 800px; }}
            h1 {{ font-size: 3.5rem; font-weight: 800; letter-spacing: -2px; margin: 0; }}
            
            .controls {{ position: sticky; top: 20px; z-index: 100; max-width: 800px; margin: 0 auto 4rem; background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(10px); padding: 25px; border-radius: 20px; border: 1px solid #334155; box-shadow: 0 20px 40px rgba(0,0,0,0.4); }}
            .search-box {{ width: 100%; padding: 1rem; border-radius: 12px; border: 1px solid #334155; background: #0f172a; color: white; font-size: 1.1rem; margin-bottom: 20px; outline: none; }}
            
            .slider-container {{ display: flex; align-items: center; gap: 20px; }}
            .slider {{ flex-grow: 1; accent-color: var(--accent); cursor: pointer; }}
            .vram-display {{ min-width: 120px; font-weight: 800; color: var(--accent); font-size: 1.2rem; }}

            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; max-width: 1200px; margin: auto; }}
            .card {{ background: var(--card); border: 1px solid #334155; padding: 1.5rem; border-radius: 16px; text-decoration: none; color: inherit; transition: 0.3s; display: flex; flex-direction: column; }}
            .card:hover {{ transform: translateY(-5px); border-color: var(--accent); background: #26334d; }}
            .gpu-tag {{ color: var(--accent); font-weight: 800; font-size: 0.7rem; text-transform: uppercase; }}
            .model-name {{ font-size: 1.1rem; font-weight: 600; margin: 10px 0; }}
            .vram-req {{ font-size: 0.8rem; color: #94a3b8; }}
            .disabled {{ opacity: 0.15; filter: grayscale(1); pointer-events: none; }}
        </style>
    </head>
    <body>
        <div class="hero">
            <h1>VRAM<span style="color:var(--accent)">.wiki</span></h1>
            <p style="color:#94a3b8">The AI Hardware Matchmaker</p>
        </div>

        <div class="controls">
            <input type="text" id="search" class="search-box" placeholder="Search Model or GPU...">
            <div class="slider-container">
                <span>Your VRAM:</span>
                <input type="range" id="vram-slider" class="slider" min="4" max="48" value="24">
                <span class="vram-display" id="vram-val">24 GB</span>
            </div>
        </div>

        <div class="grid" id="list">{''.join(links)}</div>

        <script>
            const search = document.getElementById('search');
            const slider = document.getElementById('vram-slider');
            const vramVal = document.getElementById('vram-val');
            const cards = document.querySelectorAll('.card');

            function filter() {{
                let query = search.value.toLowerCase();
                let limit = parseFloat(slider.value);
                vramVal.innerText = limit + " GB";

                cards.forEach(card => {{
                    let req = parseFloat(card.getAttribute('data-vram'));
                    let text = card.textContent.toLowerCase();
                    
                    // Filter logic: Must match search AND be under the VRAM limit
                    if (text.includes(query)) {{
                        card.style.display = 'flex';
                        if (req > limit) {{
                            card.classList.add('disabled');
                        }} else {{
                            card.classList.remove('disabled');
                        }}
                    }} else {{
                        card.style.display = 'none';
                    }}
                }});
            }}

            search.oninput = filter;
            slider.oninput = filter;
            filter(); // Run on load
        </script>
    </body>
    </html>
    """
    with open("docs/index.html", "w") as f:
        f.write(index_html)
    
    # Sitemap
    sitemap_xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{base_url}/index.html</loc></url>{"".join([f"<url><loc>{u}</loc></url>" for u in sitemap_urls])}</urlset>'
    with open("docs/sitemap.xml", "w") as f:
        f.write(sitemap_xml)
    conn.close()

if __name__ == "__main__":
    run_build()