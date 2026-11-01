"""Controlled role-ellipsis stimuli for deterministic parser equivalence testing.

These do not measure human comprehension or spoken duration.
"""
import json
from pathlib import Path
out=[]
def add(english, full, compact, subjects, objects=(), recipients=()):
    out.append({'meaning': english, 'explicit': full, 'compact': compact,
                'context': {'subjects':list(subjects), 'objects':list(objects),
                            'recipients':list(recipients)}})
add('I will send you the message tomorrow', 'Mi fu dak mel to ti sun.', 'Fu dak sun.', ['mi'], ['mel'], ['ti'])
add('I received the message', 'Mi pa ton mel.', 'Pa ton mel.', ['mi'], ['mel'])
add('You saw the garden', 'Ti pa lin pal.', 'Pa lin pal.', ['ti'], ['pal'])
add('I see the hill', 'Mi lin pál.', 'Lin pál.', ['mi'], ['pál'])
add('You went', 'Ti pa gos.', 'Pa gos.', ['ti'])
add('We will arrive tomorrow', 'Ni fu kon sun.', 'Fu kon sun.', ['ni'])
add('I am speaking now', 'Mi du vak nal.', 'Du vak nal.', ['mi'])
add('I found the message', 'Mi pa fen mel.', 'Pa fen.', ['mi'], ['mel'])
add('I do not understand the message', 'Mi ne sen mel.', 'Ne sen.', ['mi'], ['mel'])
add('You will need water', 'Ti fu rin sil.', 'Fu rin sil.', ['ti'], ['sil'])
add('I sent the message to you', 'Mi pa dak mel to ti.', 'Pa dak.', ['mi'], ['mel'], ['ti'])
add('I trust you', 'Mi vén ti.', 'Vén ti.', ['mi'], ['ti'])
add('I remembered the message', 'Mi pa pái mel.', 'Pa pái.', ['mi'], ['mel'])
add('You are doing the task', 'Ti du tas hai.', 'Du tas.', ['ti'], ['hai'])
add('I see the clear message', 'Mi lin mel kal.', 'Lin mel kal.', ['mi'], ['mel'])
add('You will go tomorrow', 'Ti fu gos sun.', 'Fu gos sun.', ['ti'])
add('I will arrive tomorrow', 'Mi fu kon sun.', 'Fu kon sun.', ['mi'])
add('You found the garden', 'Ti pa fen pal.', 'Pa fen pal.', ['ti'], ['pal'])
add('I needed water', 'Mi pa rin sil.', 'Pa rin.', ['mi'], ['sil'])
add('I do not see the hill', 'Mi ne lin pál.', 'Ne lin pál.', ['mi'], ['pál'])
add('You will send me the message tomorrow', 'Ti fu dak mel to mi sun.', 'Fu dak sun.', ['ti'], ['mel'], ['mi'])
add('I understood the message', 'Mi pa sen mel.', 'Pa sen.', ['mi'], ['mel'])
add('I will not be sending you the message tomorrow', 'Mi fu du ne dak mel to ti sun.', 'Fu du ne dak sun.', ['mi'], ['mel'], ['ti'])
add('Did you not receive the message?', 'Ti pa ne ton mel ke?', 'Pa ne ton ke?', ['ti'], ['mel'])
path=Path(__file__).resolve().parent/'data/stimuli.json'
path.write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(len(out), 'stimuli', path)
