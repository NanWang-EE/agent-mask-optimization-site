"""Package exported JSON and prompt instructions for buildless/offline viewing."""
import json
from pathlib import Path
site = Path(__file__).resolve().parents[1]
files = {'series': 'trajectories.json', 'baselines': 'baselines.json', 'example': 'example.json'}
data = {key: json.loads((site / 'data' / name).read_text()) for key, name in files.items()}
data['prompt'] = (site / 'data/prompt-instructions.txt').read_text()
(site / 'data/site-data.js').write_text('window.MASK_DATA = ' + json.dumps(data, ensure_ascii=False) + ';\n')
