import sqlite3, os, datetime
from jinja2 import Template

# --- INDIVIDUAL AUDIT PAGE (THE "ENGINE ROOM") ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VRAM.wiki | {{ gpu_name }} Audit</title>
    <style>
        :root { --bg: #050505; --neon: #00f2ff; --warn: #ff0055; --card: rgba(20, 20, 20, 0.8); }
        body { background: var(--bg); color: #fff; font-family: 'JetBrains Mono', monospace; margin: 0; display: flex; align-items: center; justify-content: center; min-height: 100vh; overflow: hidden; }
        .hud { border: 2px solid var(--neon); padding: 40px; border-radius: 5px; background: var(--card); box-shadow: 0 0 20px rgba(0, 242, 255, 0.2); max-width: 600px; position: relative; }
        .hud::before { content: "SYSTEM_DIAGNOSTIC_v2.5"; position: absolute; top: -12px; left: 20px; background: var(--bg); padding: 0 10px; color: var(--neon); font-size: 10px; }
        .header { border-bottom: 1px solid #333; margin-bottom: 30px; padding-bottom: 20px; }
        .gpu-title { font-size: 24px; text-transform: uppercase; letter-spacing: 5px; }
        .stat-row { display: flex; justify-content: space-between; margin: 15px 0; padding: 10px; background: rgba(255,255,255,0.03); border-left: 3px solid var(--neon); }
        .val { font-weight: bold; color: var(--neon); }
        .status-box { text-align: center; margin-top: 30px; padding: 20px; border: 1px dashed #444; }
        .btn { display: block; border: 1px solid var(--neon); color: var(--neon); text-decoration: none; text-align: center; padding: 15px; margin-top: 30px; transition: 0.3s; }
        .btn:hover { background: var(--neon); color: #000; box-shadow: 0 0 30px var(--neon); }
    </style>
</head>
<body>
    <div class="hud">
        <div class="header">
            <div class="gpu-title">{{ gpu_name }}</div>
            <div style="font-size: 10px; color: #666;">TARGET: {{ model_name }}</div>
        </div>
        {% for r in results %}
        <div class="stat-row">
            <span>QUANT: {{ r.bit }}-BIT</span>
            <span class="val">{{ r.needed }}GB</span>
            <span style="color: {{ '#00ff00' if 'YES' in r.status else '#ff0000' }}">{{ r.status }}</span>
        </div>
        {% endfor %}
        <a href="#" class="btn">ACQUIRE HARDWARE VIA AMAZON_NODE</a>
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
            baseline_vram = 0
            for bit in [4, 8, 16]:
                needed = round(((m['params_b'] * bit) / 8) * 1.25 + 0.6, 1)
                if bit == 4: baseline_vram = needed
                results.append({"bit": bit, "needed": needed, "status": "PASS" if h['vram_gb'] >= needed else "FAIL"})
            
            slug = f"{h['id']}-vs-{m['id'].replace('/', '-')}.html".lower()
            with open(f"docs/{slug}", "w") as f:
                f.write(Template(HTML_TEMPLATE).render(
                    model_name=m['id'], gpu_name=h['name'], vram_total=h['vram_gb'], 
                    results=results, date=2025
                ))
            
            links.append(f'''
                <a href="{slug}" class="item" data-vram="{baseline_vram}">
                    <div class="glitch-box">
                        <span class="g-name">{h['name']}</span>
                        <span class="m-name">{m['id']}</span>
                    </div>
                    <div class="r-val">{baseline_vram}GB</div>
                </a>''')
            sitemap_urls.append(f"{base_url}/{slug}")

    # --- THE TERMINAL INDEX ---
   # --- THE "ZERO-STATE" TERMINAL INDEX ---
    index_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>VRAM_WIKI // COMMAND_CENTER</title>
        <style>
            :root {{ --neon: #00f2ff; --bg: #050505; }}
            body {{ background: var(--bg); color: var(--neon); font-family: 'Courier New', monospace; margin: 0; height: 100vh; display: flex; flex-direction: column; align-items: center; overflow-x: hidden; }}
            
            .vignette {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: radial-gradient(circle, transparent 20%, black 120%); pointer-events: none; }}
            
            .search-zone {{ margin-top: 20vh; text-align: center; width: 80%; max-width: 800px; z-index: 10; transition: 0.5s ease; }}
            .search-zone.active {{ margin-top: 5vh; }}

            h1 {{ font-size: 3rem; letter-spacing: 10px; text-shadow: 0 0 20px var(--neon); margin-bottom: 40px; }}
            
            .cmd-input {{ background: transparent; border: 2px solid var(--neon); color: var(--neon); padding: 20px; width: 100%; font-size: 1.5rem; font-family: inherit; outline: none; box-shadow: inset 0 0 10px rgba(0, 242, 255, 0.2); }}
            
            .slider-box {{ margin-top: 20px; display: flex; align-items: center; gap: 20px; opacity: 0.7; font-size: 0.8rem; }}
            input[type=range] {{ flex-grow: 1; accent-color: var(--neon); }}

            /* RESULTS - INITIALLY HIDDEN */
            #list {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; width: 90%; max-width: 1200px; margin-top: 50px; opacity: 0; transition: 0.5s; pointer-events: none; }}
            #list.visible {{ opacity: 1; pointer-events: auto; }}

            .item {{ border: 1px solid #111; padding: 20px; text-decoration: none; color: inherit; background: rgba(10, 10, 10, 0.8); position: relative; transition: 0.2s; }}
            .item:hover {{ border-color: var(--neon); background: #00151a; box-shadow: 0 0 15px var(--neon); }}
            .g-name {{ font-size: 10px; opacity: 0.5; display: block; }}
            .m-name {{ font-size: 16px; display: block; margin-top: 5px; color: #fff; }}
            .r-val {{ position: absolute; right: 20px; top: 50%; transform: translateY(-50%); font-weight: bold; border: 1px solid #333; padding: 5px 10px; }}
            
            .disabled {{ opacity: 0.1; filter: blur(3px); grayscale(1); }}
        </style>
    </head>
    <body>
        <div class="vignette"></div>
        
        <div class="search-zone" id="search-zone">
            <h1>VRAM.WIKI</h1>
            <input type="text" id="search" class="cmd-input" placeholder="ENTER_HARDWARE_OR_MODEL_..." autofocus>
            <div class="slider-box">
                <span>LOCAL_VRAM_LIMIT:</span>
                <input type="range" id="vram-slider" min="4" max="48" value="24">
                <span id="vram-val">24GB</span>
            </div>
        </div>

        <div id="list">{''.join(links)}</div>

        <script>
            const search = document.getElementById('search');
            const zone = document.getElementById('search-zone');
            const list = document.getElementById('list');
            const slider = document.getElementById('vram-slider');
            const vramVal = document.getElementById('vram-val');
            const items = document.querySelectorAll('.item');

            function filter() {{
                let q = search.value.toLowerCase();
                let lim = parseFloat(slider.value);
                vramVal.innerText = lim + "GB";

                if (q.length > 0) {{
                    zone.classList.add('active');
                    list.classList.add('visible');
                }} else {{
                    zone.classList.remove('active');
                    list.classList.remove('visible');
                }}

                items.forEach(i => {{
                    let req = parseFloat(i.getAttribute('data-vram'));
                    let match = i.textContent.toLowerCase().includes(q);
                    i.style.display = match ? 'block' : 'none';
                    i.classList.toggle('disabled', req > lim);
                }});
            }}
            
            search.oninput = filter;
            slider.oninput = filter;
        </script>
    </body>
    </html>
    """
    with open("docs/index.html", "w") as f:
        f.write(index_html)
    conn.close()

if __name__ == "__main__":
    run_build()