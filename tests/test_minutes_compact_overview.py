"""Offline checks for the explicitly experimental combined overview."""
import copy
import pytest
from engine.minutes_overview import build_overview
from engine.minutes_evidence import render_minutes

def theme(i):
    return {'title_es':f'Tema de preparación {i}','title_en':f'Preparation topic {i}',
            'summary_es':f'La explicación completa del tema {i} incluye detalles importantes y condiciones.',
            'summary_en':f'The complete explanation of topic {i} includes important details and conditions.',
            'sources':[{'source_id':i,'timestamp':'00:00:01','quote':f'Fragmento {i}.'}]}

def notice(i):
    return {'category':'notice','owner':None,'due':None,
            'text_es':'Aviso: la exposición será el viernes.',
            'text_en':'Announcement: the exhibition is on Friday.',
            'sources':[{'source_id':i,'timestamp':'00:00:02','quote':'Aviso: la exposición será el viernes.'}]}

@pytest.mark.parametrize('lang',['es','en'])
def test_only_combined_explicit_option_compacts(lang):
    themes=[theme(i) for i in range(1,9)]
    items=[notice(9)]
    old=build_overview(items,themes,lang)
    new=build_overview(items,themes,lang,compact_combined=True)
    assert len(' '.join(new))<len(' '.join(old))
    assert all(t['summary_'+lang] not in ' '.join(new) for t in themes)
    assert items[0]['text_'+lang] not in ' '.join(new)
    assert build_overview(items,themes,lang,detail_included=False,compact_combined=True)==build_overview(items,themes,lang,detail_included=False)
    assert '5' in ' '.join(new) and '8' in ' '.join(new)

@pytest.mark.parametrize('lang',['es','en'])
def test_render_preserves_everything_below_overview(lang):
    themes=[theme(i) for i in range(1,9)]
    items=[notice(9)]
    original=copy.deepcopy((themes,items))
    kw=dict(editorial=themes,editorial_gaps=[{'source_id':10,'timestamp':'00:00:03','quote':'Una frase pendiente de revisión.'}],respect_mode=True,show_timestamps=False)
    old=render_minutes(items,'both',lang,executive_overview={lang:build_overview(items,themes,lang)},**kw)
    new=render_minutes(items,'both',lang,executive_overview={lang:build_overview(items,themes,lang,compact_combined=True)},**kw)
    heading='## Temas tratados' if lang=='es' else '## Topics discussed'
    assert old[old.index(heading):]==new[new.index(heading):]
    assert (themes,items)==original
    assert len(new)<len(old)

def test_counts_do_not_imply_unique_events_or_completion():
    result=build_overview([notice(1),notice(2)],[],'es',compact_combined=True)
    assert result==['Registros por categoría: avisos: 2. Consulta las secciones correspondientes para su contenido y citas.']

def test_deduplicate_title_inventory_without_altering_themes():
    themes=[theme(1),theme(2)]
    themes[1]['title_es']=themes[0]['title_es'].upper()
    result=build_overview([],themes,'es',compact_combined=True)
    assert '1 de 1' in ' '.join(result)
    assert len(themes)==2

def test_long_titles_never_exceed_inventory_bound_or_truncate_text():
    themes=[theme(1)]
    themes[0]['title_es']='X'*361
    result=build_overview([],themes,'es',compact_combined=True)
    assert len(result)==1 and '0 de 1' in result[0]
    assert not build_overview([],[],'es',compact_combined=True)
