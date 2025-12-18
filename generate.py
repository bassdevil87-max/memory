import sqlite3, os, json
from jinja2 import Template

def run_build():
    conn = sqlite3.connect('monopoly.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    os.makedirs('docs', exist_ok=True)
    
    models = [dict(row) for row in c.execute("SELECT * FROM models").fetchall()]
    hardware = [dict(row) for row in c.execute("SELECT * FROM hardware").fetchall()]
    
    # Pre-calculate data for the "Better than the Reference" Instant Search
    # This embeds the logic into the JS so it's lightning fast
    db_dump = []
    for h in hardware:
        for m in models:
            db_dump.append({
                "gpu": h['name'],
                "vram": h['vram_gb'],
                "model": m['id'],
                "task": m['task'],
                "params": m['params_b'],
                "slug": f"{h['id']}-vs-{m['id'].replace('/', '-')}.html".lower()
            })

    # --- THE "GLASS-WORKSTATION" INDEX ---
    index_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VRAM.wiki | Intelligent Hardware Auditor</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            :root {{ --bg: #0a0a0c; --panel: #141417; --accent: #00f2ff; --border: #222226; --text: #e0e0e0; }}
            body {{ background: var(--bg); color: var(--text); font-family: 'Inter', system-ui, sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; }}
            
            /* LEFT INPUT PANEL */
            .sidebar {{ width: 400px; background: var(--panel); border-right: 1px solid var(--border); padding: 2rem; display: flex; flex-direction: column; gap: 1.5rem; }}
            h1 {{ font-size: 1.5rem; letter-spacing: -1px; margin: 0 0 1rem 0; color: #fff; }}
            label {{ font-size: 0.75rem; text-transform: uppercase; color: #666; letter-spacing: 1px; font-weight: bold; }}
            select, input {{ background: #000; border: 1px solid var(--border); color: #fff; padding: 12px; border-radius: 8px; width: 100%; outline: none; }}
            select:focus {{ border-color: var(--accent); }}

            /* RIGHT ANALYTICS PANEL */
            .main-stage {{ flex-grow: 1; padding: 3rem; display: flex; align-items: center; justify-content: center; background: radial-gradient(circle at center, #16161a 0%, #0a0a0c 100%); }}
            .audit-card {{ width: 100%; max-width: 900px; display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; align-items: center; }}
            
            /* THE RING */
            .visual-center {{ position: relative; width: 300px; height: 300px; margin: auto; }}
            #vramChart {{ filter: drop-shadow(0 0 15px rgba(0, 242, 255, 0.2)); }}
            .chart-label {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; }}
            .chart-label span {{ display: block; font-size: 0.8rem; color: #666; }}
            .chart-label b {{ font-size: 2.5rem; color: #fff; }}

            /* DATA GRID */
            .metrics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
            .metric-box {{ background: rgba(255,255,255,0.02); border: 1px solid var(--border); padding: 1.5rem; border-radius: 12px; }}
            .metric-box small {{ display: block; color: #666; margin-bottom: 5px; font-size: 0.7rem; text-transform: uppercase; }}
            .metric-box span {{ font-size: 1.2rem; font-weight: bold; color: var(--accent); }}
            
            .status-tag {{ grid-column: span 2; text-align: center; padding: 10px; border-radius: 6px; font-weight: 900; letter-spacing: 2px; }}
            .pass {{ background: rgba(0, 242, 255, 0.1); color: var(--accent); border: 1px solid var(--accent); }}
            .fail {{ background: rgba(255, 0, 85, 0.1); color: #ff0055; border: 1px solid #ff0055; }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h1>VRAM<span style="color:var(--accent)">.WIKI</span></h1>
            
            <div>
                <label>Select GPU Hardware</label>
                <select id="gpu-select">
                    {''.join([f'<option value="{h["name"]}" data-vram="{h["vram_gb"]}">{h["name"]} ({h["vram_gb"]}GB)</option>' for h in hardware])}
                </select>
            </div>

            <div>
                <label>Target AI Model</label>
                <select id="model-select">
                    {''.join([f'<option value="{m["id"]}" data-params="{m["params_b"]}">{m["id"]}</option>' for m in models])}
                </select>
            </div>

            <div>
                <label>Quantization (Precision)</label>
                <select id="quant-select">
                    <option value="4">4-bit (Compressed)</option>
                    <option value="8">8-bit (Balanced)</option>
                    <option value="16">16-bit (Full Precision)</option>
                </select>
            </div>

            <div style="margin-top: auto; font-size: 0.7rem; color: #444;">
                VERSION 2.0 // DECENTRALIZED DATA NODE
            </div>
        </div>

        <div class="main-stage">
            <div class="audit-card">
                <div class="visual-center">
                    <canvas id="vramChart"></canvas>
                    <div class="chart-label">
                        <span id="percent-label">0%</span>
                        <b id="total-val">0 GB</b>
                    </div>
                </div>

                <div class="metrics">
                    <div id="status-tag" class="status-tag">INITIALIZING...</div>
                    <div class="metric-box">
                        <small>Required VRAM</small>
                        <span id="req-vram">0.0 GB</span>
                    </div>
                    <div class="metric-box">
                        <small>System Headroom</small>
                        <span id="headroom">0.0 GB</span>
                    </div>
                    <div class="metric-box">
                        <small>Model Params</small>
                        <span id="param-count">0B</span>
                    </div>
                    <div class="metric-box">
                        <small>Context Buffer</small>
                        <span>1.2 GB</span>
                    </div>
                    <a href="#" id="deep-link" style="grid-column: span 2; color: var(--accent); text-align: center; text-decoration: none; font-size: 0.8rem; border: 1px solid var(--border); padding: 10px; border-radius: 8px;">View Full Technical Audit →</a>
                </div>
            </div>
        </div>

        <script>
            const ctx = document.getElementById('vramChart').getContext('2d');
            let chart = new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    datasets: [{{
                        data: [0, 100],
                        backgroundColor: ['#00f2ff', '#1a1a1c'],
                        borderWidth: 0,
                        circumference: 270,
                        rotation: 225,
                        cutout: '85%'
                    }}]
                }},
                options: {{ plugins: {{ tooltip: {{ enabled: false }} }} }}
            }});

            function update() {{
                const gpu = document.getElementById('gpu-select');
                const model = document.getElementById('model-select');
                const quant = document.getElementById('quant-select').value;
                
                const vram_total = parseFloat(gpu.options[gpu.selectedIndex].dataset.vram);
                const params = parseFloat(model.options[model.selectedIndex].dataset.params);
                
                // 500 IQ Calculation: (Params * Bits / 8) * Overhead + System Base
                const needed = ((params * quant) / 8) * 1.2 + 0.8;
                const percent = Math.min((needed / vram_total) * 100, 100).toFixed(1);
                
                document.getElementById('total-val').innerText = needed.toFixed(1) + " GB";
                document.getElementById('percent-label').innerText = percent + "% VRAM";
                document.getElementById('req-vram').innerText = needed.toFixed(1) + " GB";
                document.getElementById('headroom').innerText = (vram_total - needed).toFixed(1) + " GB";
                document.getElementById('param-count').innerText = params + "B";
                
                const tag = document.getElementById('status-tag');
                if (needed <= vram_total) {{
                    tag.innerText = "COMPATIBLE";
                    tag.className = "status-tag pass";
                    chart.data.datasets[0].backgroundColor[0] = '#00f2ff';
                }} else {{
                    tag.innerText = "INSUFFICIENT VRAM";
                    tag.className = "status-tag fail";
                    chart.data.datasets[0].backgroundColor[0] = '#ff0055';
                }}
                
                chart.data.datasets[0].data = [percent, 100 - percent];
                chart.update();
            }}

            document.querySelectorAll('select').forEach(s => s.onchange = update);
            update();
        </script>
    </body>
    </html>
    """
    with open("docs/index.html", "w") as f:
        f.write(index_html)
    conn.close()

if __name__ == "__main__":
    run_build()