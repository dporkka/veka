"""Generate preregistration-ready trial definitions; no audio or observations."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
original=json.loads((ROOT/'data/stimuli.json').read_text(encoding='utf8'))
items=[]
for i,item in enumerate(original):
    items.append(dict(item_id=f'ellipsis-{i+1:02d}',category='ellipsis',
        meaning=item['meaning'],explicit=item['explicit'],compact=item['compact'],
        context=item['context'],critical=0))
# Deliberately noncompressible controls. A compact policy must not force omission.
controls=[
 ('The person went','Ren pa gos.'),
 ('I did not go','Mi pa ne gos.'),
 ('You will speak','Ti fu vak.'),
 ('Two people went','Ren wen kuk pa gos.'),
 ('Three people went','Ren wen zun pa gos.'),
 ('The message is clear','Mel es kal.'),
 ('I need water','Mi rin sil.'),
 ('The person will arrive','Ren fu kon.'),
]
for i,(meaning,utterance) in enumerate(controls):
    items.append(dict(item_id=f'control-{i+1:02d}',category='uncompressible_control',
        meaning=meaning,explicit=utterance,compact=utterance,
        context={'subjects':[], 'objects':[], 'recipients':[]},
        critical=int(i in (3,4))))
(ROOT/'data/study_items_v03.json').write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(f'Wrote {len(items)} study stimuli (24 compression pairs + 8 controls).')
