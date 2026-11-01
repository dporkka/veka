"""Reproducible construction of 100 canonical CONCEPTS, not donor evidence.

Generates only a frozen research queue, never changes data/lexicon.csv.
"""
import csv
from collections import defaultdict
from pathlib import Path

BASE=Path(__file__).resolve().parent
OUT=BASE/'data/international_candidates_v04.csv'
SEEDS=[
 ('data','noun','da-ta','data'),
 ('music','noun','mu-si-ka','musica'),
 ('language','noun','lin-gu-a','lingua'),
 ('information','noun','in-fo-ma-si-on','informacion'),
 ('computer','noun','ko-pu-ta','computador'),
 ('rice','noun','ri-se','rice'),
 ('digital','adjective','di-gi-tal','digital'),
 ('school','noun','se-ko-la','escola'),
]
with (BASE/'data/lexicon.csv').open(encoding='utf8',newline='') as f:
    roots=[r for r in csv.DictReader(f) if r['kind']=='root' and r['pos'] in ('noun','verb','adjective')]
by_concept={(r['gloss'],r['pos']):r for r in roots}
selected=[];seen=set()
for gloss,pos,form,reference in SEEDS:
    r=by_concept[(gloss,pos)]
    selected.append((r,form,reference));seen.add(r['form'])
# Round-robin the remaining candidates by part of speech and semantic domain.
# This avoids silently treating ten Romance-friendly examples as representative.
groups=defaultdict(list)
for r in roots:
    if r['form'] not in seen:
        groups[(r['pos'],r['domain'])].append(r)
for k in groups:groups[k].sort(key=lambda r:(r['gloss'],r['form']))
while len(selected)<100:
    more=False
    for key in sorted(groups):
        if len(selected)>=100:break
        if groups[key]:
            r=groups[key].pop(0)
            selected.append((r,'',''))
            more=True
    if not more:raise ValueError('not enough canonical concepts')
fields=['concept_id','gloss','pos','core_form','domain','candidate_form','reference_spelling','status','evidence_note']
with OUT.open('w',encoding='utf8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for i,(r,proposal,reference) in enumerate(selected,1):
        w.writerow(dict(concept_id=f'C{i:03d}',gloss=r['gloss'],pos=r['pos'],
                        core_form=r['form'],domain=r['domain'],candidate_form=proposal,
                        reference_spelling=reference,
                        status='unverified_draft' if proposal else 'not_proposed',
                        evidence_note=('Illustrative orthographic inspiration only; NOT verified donor attestation or recognition data.' if proposal else 'Donor evidence and proposed form not supplied.')))
print(f'Wrote {len(selected)} concepts; {len(SEEDS)} illustrative experimental draft forms; no canonical changes')
