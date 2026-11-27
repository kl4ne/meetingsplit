from engine.minutes_evidence import source_blocks
from engine.minutes_theme_presentation import compact_repeated_theme_sources
from engine.minutes_overview import build_overview

BASE='The discussion continued with background on file naming, the archive layout, and examples in the reference guide.'
def theme(title,rows):
    return {'title_es':title,'summary_es':title+'.',
            'sources':[{'source_id':r['id'],'timestamp':r['timestamp'],'quote':r['text'].strip()} for r in rows]}

def test_repeated_split_line_themes_accounted_without_discarding_raw_themes():
    text='[00:00:01] '+BASE+'\n[00:02:00] '+(BASE+' ')*35+BASE[:12]
    blocks=list(source_blocks(text));rows=[r for b in blocks for r in b]
    themes=[theme('Archivo',[rows[0]]),theme('Repetición',[rows[1]]),theme('Continuación',[rows[-1]])]
    retained,omitted=compact_repeated_theme_sources(blocks,themes)
    assert retained==themes[:1] and len(omitted)==2
    assert all(x['matches'][0]['earlier_source_id']==1 for x in omitted)
    assert len(themes)==3

def test_unique_tail_or_ordinary_subset_theme_is_never_removed():
    text='[00:00:01] '+BASE+'\n[00:02:00] '+(BASE+' ')*35+'Se revisó otro archivo.'
    blocks=list(source_blocks(text));rows=[r for b in blocks for r in b]
    themes=[theme('Archivo',[rows[0]]),theme('Detalle',[rows[0]]),theme('Continuación',[rows[-1]])]
    assert compact_repeated_theme_sources(blocks,themes)==(themes,[])

def test_single_incomplete_prefix_is_not_treated_as_repeated_long_line():
    blocks=list(source_blocks('[00:00:01] '+BASE+'\n[00:02:00] '+BASE[:26]))
    rows=[r for b in blocks for r in b]
    themes=[theme('Archivo',[rows[0]]),theme('Fragmento',[rows[1]])]
    assert compact_repeated_theme_sources(blocks,themes)==(themes,[])

def test_spanish_summary_does_not_reinsert_english_weekday():
    item={'category':'action','owner':'Ana Ruiz','due':'Friday','text_es':'Ana Ruiz enviará el borrador a más tardar el viernes.',
          'sources':[{'source_id':1,'timestamp':'00:00:01','quote':'Ana Ruiz will send the draft by Friday.'}]}
    report=' '.join(build_overview([item],[],'es'))
    assert 'viernes' in report and 'Friday' not in report
