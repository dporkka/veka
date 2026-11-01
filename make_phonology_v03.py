"""Create reproducible structural audit and non-tonal experimental word variants."""
import csv
import itertools
import json
from pathlib import Path
from veka.core import Lexicon,validate_word,syllabify
from veka.phonology import analyze_root_confusions

ROOT=Path(__file__).resolve().parent
L=Lexicon.from_csv(ROOT/'data/lexicon.csv')
audit=analyze_root_confusions(L)
(ROOT/'data/phonology_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
# Only alternate ablation materials; preserve the canonical dictionary exactly.
proposals={'pái':'fok', 'pál':'lek','lé':'hok','vén':'gon'}
with (ROOT/'data/tone_free_ablation.csv').open('w',newline='',encoding='utf8') as f:
    writer=csv.DictWriter(f,fieldnames=('tonal_form','toneless_candidate','gloss','status'))
    writer.writeheader()
    for old,new in proposals.items():
        assert old in L and new not in L and validate_word(new) and not any(a in new for a in 'áéíóú')
        writer.writerow({'tonal_form':old,'toneless_candidate':new,'gloss':L[old].gloss,
                         'status':'unvalidated experimental replacement'})
print(f"Audit: {audit['minimal_pair_count']} structural minimal pairs; "
      f"{audit['root_count']} audited roots; {len(proposals)} tone-free alternatives")
