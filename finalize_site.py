import sqlite3, os
from jinja2 import Template

# ADDING PRO FEATURES: Breadcrumbs, Social Tags, and Expert Bylines
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ gpu_name }} + {{ model_name }} | VRAM & Performance Guide</title>
    <meta property="og:title" content="Run {{ model_name }} on {{ gpu_name }}">
    <meta property="og:description" content="Calculate if your {{ gpu_name }} can handle {{ model_name }} with 4-bit, 8-bit, and 16-bit quantization.">
    <meta property="og:type" content="article">
    
    <style>
        :root { --primary: #3b82f6; --dark: #030712; --card: #111827; }
        body { background: var(--dark); color: #e5e7eb; font-family: 'Inter', sans-serif; line-height: 1.6; padding: 20px; }
        .breadcrumb { font-size: 0.8rem; color: #9ca3af; margin-bottom: 20px; }
        .breadcrumb a { color: var(--primary); text-decoration: none; }
        .author-box { border-top: 1px solid #374151; margin-top: 40px; padding-top: 20px; font-size: 0.9rem; color: #9ca3af; }
        .card { background: var(--card); border: 1px solid #374151; border-radius: 12px; padding: 30px; max-width: 800px; margin: auto; }
        .result-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .result-table th { text-align: left; border-bottom: 1px solid #374151; padding: 10px; }
        .result-table td { padding: 10px; border-bottom: 1px solid #1f2937; }
        .btn { display: inline-block; background: var(--primary); color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600; }
    </style>
</head>
<body>
    <div class="card">
        <div class="breadcrumb">
            <a href="index.html">Home</a> > <a href="#">{{ gpu_name }}</a> > {{ model_name }}
        </div>

        <h1>{{ model_name }} Compatibility Guide</h1>
        <p>Expert analysis for running <b>{{ model_name }}</b> on <b>{{ gpu_name }}</b>.</p>

        <table class="result-table">
            <thead>
                <tr><th>Quantization</th><th>VRAM Needed</th><th>Status</th></tr>
            </thead>
            <tbody>
                {% for r in results %}
                <tr>
                    <td>{{ r.bit }}-bit</td>
                    <td>{{ r.needed }} GB</td>
                    <td style="color: {{ 'green' if 'YES' in r.status else 'red' }}">{{ r.status }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <a href="{{ cta_link }}" class="btn">View Current {{ gpu_name }} Pricing</a>

        <div class="author-box">
            <p><b>Editorial Note:</b> This report was generated using the 2025 AI-Monopoly Physics Engine. Calculations assume a 25% KV-cache overhead for long-context windows.</p>
        </div>
    </div>
</body>
</html>
"""

def build_final():
    conn = sqlite3.connect('monopoly.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    os.makedirs('docs', exist_ok=True)
    
    models = c.execute("SELECT * FROM models").fetchall()
    gpus = c.execute("SELECT * FROM hardware").fetchall()
    
    for h in gpus:
        for m in models:
            results = []
            for bit in [4, 8, 16]:
                needed = round(((m['params_b'] * bit) / 8) * 1.25 + 0.6, 1)
                results.append({"bit": bit, "needed": needed, "status": "✅ YES" if h['vram_gb'] >= needed else "❌ NO"})
            
            slug = f"{h['id']}-vs-{m['id'].replace('/', '-')}.html".lower()
            with open(f"docs/{slug}", "w") as f:
                f.write(Template(HTML_TEMPLATE).render(
                    model_name=m['id'], gpu_name=h['name'], brand=h['brand'], 
                    price=h['price'], params=m['params_b'], task=m['task'], 
                    license=m['license'], results=results, cta_link="#"
                ))
    conn.close()

if __name__ == "__main__":
    build_final()
