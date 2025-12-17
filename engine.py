import sqlite3, re, os
from huggingface_hub import HfApi

def setup_all():
    # 1. Database Setup
    conn = sqlite3.connect('monopoly.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS models 
                 (id TEXT PRIMARY KEY, params_b REAL, task TEXT, license TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS hardware 
                 (id TEXT PRIMARY KEY, name TEXT, vram_gb INTEGER, price REAL, brand TEXT)''')
    
    # 2. 2025 High-Margin Inventory
    gpus = [
        ('rtx-5090', 'Nvidia RTX 5090', 32, 1999.0, 'Nvidia'), 
        ('rtx-4090', 'Nvidia RTX 4090', 24, 1599.0, 'Nvidia'),
        ('rtx-5080', 'Nvidia RTX 5080', 16, 1199.0, 'Nvidia'),
        ('mac-m4-max', 'Apple M4 Max', 128, 3999.0, 'Apple')
    ]
    c.executemany("INSERT OR REPLACE INTO hardware VALUES (?,?,?,?,?)", gpus)

    # 3. Model Mining (Pulling top 100 trending)
    print("Mining Hugging Face...")
    api = HfApi()
    models = api.list_models(sort="downloads", direction=-1, limit=100, full=True)
    for m in models:
        # 500 IQ Regex: Extract parameter count from ID (e.g., '8b' -> 8.0)
        param_match = re.search(r'(\d+\.?\d*)[Bb]', m.id)
        params = float(param_match.group(1)) if param_match else 7.0
        
        license = str(m.card_data.license) if m.card_data and hasattr(m.card_data, 'license') else "Open"
        c.execute("INSERT OR REPLACE INTO models VALUES (?,?,?,?)", 
                  (m.id, params, m.pipeline_tag or "Inference", license))
    
    conn.commit()
    conn.close()
    print("Mining Complete.")

if __name__ == "__main__":
    setup_all()