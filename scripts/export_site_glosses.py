"""Run from repository root: python3 scripts/export_site_glosses.py"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from veka.site_glosses import build_site_glosses  # noqa: E402

output = Path(__file__).resolve().parents[1] / "data/site_glosses_v01.json"
output.write_text(json.dumps(build_site_glosses(), ensure_ascii=False, indent=2) + "\n", encoding="utf8")
print(output)
