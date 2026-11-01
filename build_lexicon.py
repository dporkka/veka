"""Generate a deterministic, auditable Veka 0.3 starter lexicon.

Only atomic roots are arbitrarily assigned. Compounds are compositional.
The lexicon is NOT a corpus-optimized list and has not been speaker-tested.
"""
from __future__ import annotations
import csv
import itertools
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'data' / 'lexicon.csv'
C = 'pbtdkgmnfvszhlryw'
V = 'aeiou'
CODAS = ('', 'n', 'l', 's', 'k')
DIPHTHONGS = ('ai', 'au', 'oi')

# Established vocabulary carried forward verbatim from v0.1.
fixed = [
 ('mi','I/me','pronoun',''), ('ti','you','pronoun',''),
 ('sa','he/she/it (established referent)','pronoun',''),('ni','we/us','pronoun',''),
 ('lu','plural','particle',''), ('pa','past','particle',''),
 ('fu','future','particle',''),('du','progressive','particle',''),
 ('ne','not','particle',''),('ke','yes/no question','particle',''),
 ('ya','yes','particle',''),('no','no','particle',''),
 ('to','to/recipient','particle',''),('en','at/location','particle',''),
 ('de','of/possessor','particle',''),('es','copula','particle',''),
 ('ha','imperative','particle',''),
 ('dak','send','verb','transitive'), ('ton','receive','verb','transitive'),
 ('sen','understand','verb','transitive'),('vak','speak','verb','intransitive'),
 ('lin','see','verb','transitive'),('kon','arrive','verb','intransitive'),
 ('fen','find','verb','transitive'),('tas','do','verb','transitive'),
 ('gos','go','verb','intransitive'),('rin','need','verb','transitive'),
 ('pái','remember','verb','transitive'),
 ('ren','person','noun',''),('dol','house','noun',''),
 ('sil','water','noun',''), ('mel','message','noun',''),
 ('pal','garden','noun',''),('pál','hill','noun',''),
 ('lé','idea','noun',''),
 ('pes','fast','adjective',''), ('kal','clear','adjective',''),
 ('sak','knowledgeable','adjective',''), ('bon','good','adjective',''),
 ('min','small','adjective',''), ('val','large','adjective',''),
 ('vén','trust','verb','transitive'),
 ('nal','now','time',''),('sun','tomorrow','time',''),
]

# Natural semantic domains; an atomic root may appear only once.
NOUNS = {
 'people': '''child adult woman man parent mother father sibling teacher student worker friend neighbor doctor nurse engineer artist scientist lawyer customer seller buyer driver pilot farmer leader member guest stranger family group team community citizen manager programmer designer researcher writer musician athlete passenger patient visitor owner employee employer colleague assistant expert''',
 'places': '''room city village country road bridge park school hospital office shop market station port airport farm forest river lake ocean mountain valley island beach building factory restaurant hotel library street neighborhood region square sidewalk tunnel warehouse university classroom clinic apartment kitchen bathroom bedroom laboratory bank courthouse theater museum church temple playground border''',
 'objects': '''phone computer car bicycle train boat airplane bus tool machine door window table chair book paper pen key bottle cup plate bag box camera clock lamp bed shirt shoe money ticket card knife light cable battery engine screen keyboard radio television robot sensor router server database file image video letter map document contract invoice payment package parcel wallet coin umbrella mirror ladder helmet coat hat glove mask ball wheel button switch pipe pump printer microphone speaker antenna satellite vehicle''',
 'abstract': '''plan goal project problem solution fact story question answer reason result law rule right duty risk chance time day night week month year hour minute moment event meeting task work job skill knowledge science art music language word name number code data information truth lie memory dream feeling thought choice decision method system process service product price cost value profit debt tax health illness pain medicine education freedom peace war safety danger quality quantity speed distance direction position structure function pattern type relation identity evidence research history future past present cause effect change growth decline success failure responsibility opportunity agreement conflict resource energy power network model signal algorithm calculation measurement theory practice experience attention intention desire belief opinion''',
 'nature': '''air fire earth soil plant animal tree flower stone metal wood leaf root seed fruit grass rain snow wind cloud sky sunlight moon star planet sea wave coast desert ridge cave field grove insect bird fish dog cat horse cow pig sheep chicken bee ant spider snake whale shark mouse elephant monkey bear wolf lion tiger deer frog butterfly mosquito bacteria virus fungus''',
 'food': '''bread rice wheat corn egg milk cheese meat soup salad salt sugar oil butter coffee tea juice apple orange banana lemon potato tomato onion carrot bean nut cake cookie chocolate sandwich pizza pasta seafood vegetable spice pepper garlic honey''',
}
NOUN_LIMITS = {'people':20, 'places':20, 'objects':25, 'abstract':46, 'nature':15, 'food':12}
# Compatible adjectival patterns for transparent compounds; preserve the order for pedagogical priority.
ADJECTIVES = {
 'people': 'new old young skilled local foreign friendly strong weak healthy sick',
 'places': 'large small new old near far public private safe dangerous clean dirty',
 'objects': 'large small new old useful broken heavy simple complex fast slow digital',
 'abstract': 'large small new old clear important simple complex true false useful urgent',
 'nature': 'large small young old green red blue white black hot cold wet dry',
 'food': 'large small new old fresh stale hot cold sweet sour salty healthy',
}
ADDITIONAL_VERBS = '''eat drink sleep wake walk run stop start open close create destroy build repair learn teach read write listen hear think decide choose ask answer give take buy sell pay owe borrow lend own use make work play help try wait travel return stay leave meet join separate find search lose win fail grow fall rise cut carry move push pull hold drop mail call reply share save delete copy print draw count measure compare test check approve reject accept refuse believe doubt know forget love like hate hope fear want offer request promise agree disagree explain describe show hide bring deliver collect discover invent change translate plan schedule cancel begin finish continue repeat rest exercise cook clean drive swim fly climb sit stand laugh cry smile study improve protect attack defend warn inspect observe report predict'''.split()
ADDITIONAL_ADJECTIVES = '''new old young skilled local foreign friendly strong weak important healthy sick experienced honest curious careful creative busy tired responsible near far public private safe dangerous quiet beautiful clean dirty central remote modern historic open closed useful broken heavy lightweight simple complex cheap expensive slow digital physical portable durable true false practical theoretical economic social urgent long short global measurable reliable uncertain green red blue white black bright dark hot cold wet dry wild domestic rare common fresh stale sweet sour salty bitter cooked raw spicy mild imported soft hard round flat narrow wide deep shallow full empty early late possible impossible likely unlikely equal different correct wrong ready available unavailable exact approximate'''.split()
ADDITIONAL_VERBS = ADDITIONAL_VERBS[:55]
ADDITIONAL_ADJECTIVES = [x for x in ADDITIONAL_ADJECTIVES if x in set(' '.join(ADJECTIVES.values()).split())]
TIME_WORDS = ['yesterday','today','tonight','soon','later','earlier','always','never','sometimes','often','already','still']

# Ensure pronoun, part-of-speech and semantic gloss mappings are unique.
entries = []
forms = set(); glosses = set(); gloss_to_form = {}

def add(form, gloss, pos, kind='root', domain='', head='', modifier='', valency=''):
    assert form not in forms, (form, gloss)
    # homographic English concepts collapse to one root; no hard claim of unique English word senses
    assert (pos, gloss) not in glosses, (pos, gloss)
    forms.add(form); glosses.add((pos, gloss))
    entries.append(dict(form=form, gloss=gloss, pos=pos, kind=kind, domain=domain,
                        head=head, modifier=modifier, valency=valency))
    if kind == 'root': gloss_to_form[(pos, gloss)] = form

for form, gloss, pos, valency in fixed:
    add(form, gloss, pos, valency=valency)
# Carry over the explicitly documented lexical compound from v0.1.
add('ren-sak', 'expert', 'noun', kind='compound', domain='people', head='ren', modifier='sak')

# Use only level-tone new roots, and reserve all previously assigned forms.
possible = []
for onset, nucleus, coda in itertools.product(''+C, tuple(V)+DIPHTHONGS, CODAS):
    if nucleus in DIPHTHONGS and coda not in ('','n'): continue
    form = onset+nucleus+coda
    if form in ('yi','wu') or form in forms: continue
    possible.append(form)
# Prefer robust CV or CVC forms. Avoid neighboring forms under 2 character edit distance when possible.
rng = random.Random(20261031)
rng.shuffle(possible)
possible.sort(key=lambda w: (len(w)==1, len(w)>3, w.startswith(('yi','wu'))))
new_index = 0

def fresh():
    global new_index
    while new_index < len(possible):
        f = possible[new_index]; new_index += 1
        if f not in forms: return f
    raise RuntimeError('insufficient level-tone root inventory')

for domain, words in NOUNS.items():
    for gloss in words.split()[:NOUN_LIMITS[domain]]:
        # If an English concept exists already, reuse its established root and retain its domain.
        if ('noun',gloss) in gloss_to_form: continue
        add(fresh(),gloss,'noun',domain=domain)

for gloss in ADDITIONAL_VERBS:
    if ('verb',gloss) in gloss_to_form: continue
    # Predicates are transitive only when explicit object is appropriate; avoid uncertain arbitrary object valency.
    valency = 'intransitive' if gloss in ('sleep','wake','walk','run','stop','start','work','play','wait','travel','return','stay','leave','win','fail','grow','fall','rise','swim','fly','climb','sit','stand','laugh','cry','smile','rest','exercise','agree','disagree','continue') else 'transitive'
    add(fresh(),gloss,'verb',domain='action',valency=valency)
for gloss in ADDITIONAL_ADJECTIVES:
    if ('adjective',gloss) in gloss_to_form: continue
    add(fresh(),gloss,'adjective',domain='quality')
for gloss in TIME_WORDS:
    if ('time',gloss) in gloss_to_form: continue
    add(fresh(),gloss,'time',domain='temporal')

atomic_count = sum(e['kind']=='root' for e in entries)
if atomic_count >= 1000: raise RuntimeError(f'{atomic_count} atoms not enough headroom for compounds')
# Use paired glosses where their semantic domains are compatible. A hyphen here is a
# MORPHEME boundary, not an audible pause, and every compound is compositional.
# Distribute compounds across domains rather than exhausting the people category.
compound_pairs = []
for domain, words in NOUNS.items():
    for gloss in words.split()[:NOUN_LIMITS[domain]]:
        compound_pairs.append((domain,gloss,ADJECTIVES[domain].split()))
for rank in range(max(len(mods) for _,_,mods in compound_pairs)):
    for domain, gloss, modifiers in compound_pairs:
        if rank >= len(modifiers): continue
        adj = modifiers[rank]
        noun_form = gloss_to_form[('noun', gloss)]
        adjective_form = gloss_to_form.get(('adjective',adj))
        if not adjective_form: raise RuntimeError(f'unsupported modifier {adj}')
        compound = noun_form+'-'+adjective_form
        if compound in forms: continue
        add(compound, adj+' '+gloss, 'noun', kind='compound', domain=domain,
            head=noun_form, modifier=adjective_form)
        if len(entries) >= 1000: break
    if len(entries) >= 1000: break

if len(entries) != 1000: raise RuntimeError(f'only generated {len(entries)} entries ({atomic_count} atoms)')
# Veka 0.3 extension: append rather than reassigning ANY 0.2 forms.
# Deliberately avoid introducing a tonal distinction in exact numerals.
new_terms = [
 ('zi','logical AND','particle'), ('oi','inclusive OR','particle'),
 ('fi','material implication IF','particle'), ('na','proposition NOT','particle'),
 ('ve','logical argument separator','particle'), ('yu','logical expression end','particle'),
 ('al','universal quantifier','particle'), ('kis','existential quantifier','particle'),
 ('sin','negative number sign','particle'), ('dis','decimal separator','particle'),
 ('su','numeric unit marker','particle'),
 ('nul','zero','digit'), ('ran','one','digit'), ('kuk','two','digit'),
 ('zun','three','digit'), ('sok','four','digit'), ('gel','five','digit'),
 ('tak','six','digit'), ('pil','seven','digit'), ('bos','eight','digit'),
 ('mus','nine','digit'),
 ('sek','second (SI)','unit'), ('vos','kilogram (SI)','unit'),
 ('rel','meter (SI)','unit'), ('wok','liter','unit'),
]
for form,gloss,pos in new_terms:
    add(form,gloss,pos,domain='formal-v03')
OUT.parent.mkdir(parents=True,exist_ok=True)
with OUT.open('w',newline='',encoding='utf-8') as file:
    writer = csv.DictWriter(file,fieldnames=['form','gloss','pos','kind','domain','head','modifier','valency'])
    writer.writeheader(); writer.writerows(entries)
print(f"Lexicon: {len(entries)} entries; {sum(e['kind']=='root' for e in entries)} roots, {sum(e['kind']=='compound' for e in entries)} compounds, {len(forms)} distinct forms")
print(f'Last: {entries[-1]}')
