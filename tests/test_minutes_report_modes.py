"""Production localized-editorial presentation modes; no model inference."""
import pytest
from engine.minutes_evidence import render_minutes
from engine.minutes_overview import build_overview

REF={'source_id':1,'timestamp':'00:00:01','quote':'Se examinó la orientación.'}
GAP={'source_id':3,'timestamp':'00:00:03','quote':'Un pasaje sin síntesis.'}
ACTION={'category':'action','owner':'Ana Ruiz','due':'Friday',
        'sources':[{'source_id':2,'timestamp':'00:00:02','quote':'Ana Ruiz will send the guide by Friday.'}],
        'text_es':'Ana Ruiz enviará la guía a más tardar el viernes.',
        'text_en':'Ana Ruiz will send the guide by Friday.'}
THEMES=[{'sources':[REF],'title_es':'Orientación detallada','summary_es':'Detalle temático de orientación.',
         'title_en':'Detailed orientation','summary_en':'Detailed thematic orientation.'}]
OVERVIEW={'es':['Síntesis ejecutiva breve.'],'en':['Concise executive overview.']}

@pytest.mark.parametrize('lang,headline,summary,detail,title',[
    ('es','Resumen ejecutivo','Síntesis ejecutiva breve.','Temas tratados','Orientación detallada'),
    ('en','Executive summary','Concise executive overview.','Topics discussed','Detailed orientation'),
])
@pytest.mark.parametrize('mode',['summary','minutes','both'])
def test_distinct_modes_keep_outcomes_and_review(lang,headline,summary,detail,title,mode):
    report=render_minutes([ACTION],mode,lang,editorial=THEMES,executive_overview=OVERVIEW,
        editorial_gaps=[GAP],show_timestamps=False,respect_mode=True)
    assert (summary in report)==(mode!='minutes')
    assert (title in report)==(mode!='summary')
    assert ('## '+detail in report)==(mode!='summary')
    assert report.startswith('# '+headline) if mode=='summary' else not report.startswith('# '+headline)
    assert report.count('## '+headline)==(1 if mode=='both' else 0)
    assert 'Ana Ruiz' in report and 'Friday' in report and GAP['quote'] in report
    assert '[00:00:' not in report

def test_bilingual_summary_has_separate_documents_and_no_detailed_themes():
    report=render_minutes([ACTION],'summary','both',editorial=THEMES,executive_overview=OVERVIEW,
        editorial_gaps=[GAP],show_timestamps=False,respect_mode=True)
    es,en=report.split('\n\n---\n\n')
    assert es.startswith('# Resumen ejecutivo') and en.startswith('# Executive summary')
    assert OVERVIEW['es'][0] in es and OVERVIEW['en'][0] not in es
    assert OVERVIEW['en'][0] in en and OVERVIEW['es'][0] not in en
    assert GAP['quote'] in es and GAP['quote'] in en

def test_no_overview_does_not_drop_descriptive_content():
    report=render_minutes([],'summary','es',editorial=THEMES,respect_mode=True)
    assert THEMES[0]['summary_es'] in report

def test_legacy_mode_unchanged_by_default():
    report=render_minutes([ACTION],'summary','es',editorial=THEMES,executive_overview=OVERVIEW)
    assert THEMES[0]['title_es'] in report and OVERVIEW['es'][0] in report

def test_overview_includes_disagreement():
    item={'category':'disagreement','owner':None,'due':None,
          'sources':[{'source_id':1,'timestamp':'00:00:01','quote':'El grupo expresó desacuerdo con el horario.'}],
          'text_es':'El grupo expresó desacuerdo con el horario.',
          'text_en':'The group expressed disagreement with the schedule.'}
    assert any('Desacuerdos:' in p and 'horario' in p for p in build_overview([item],[],'es'))
    assert any('Disagreements:' in p and 'schedule' in p for p in build_overview([item],[],'en'))

@pytest.mark.parametrize('lang,label,legacy,reference',[
    ('es','Otros temas identificados','Los demás temas se desarrollan a continuación.','registro de evidencias'),
    ('en','Other identified topics','The remaining topics are detailed below.','evidence record'),
])
def test_summary_only_discloses_unsampled_topic_titles(lang,label,legacy,reference):
    themes=[{'sources':[REF],'title_'+lang:f'Title {i:02d}',
             'summary_'+lang:f'Sentence {i:02d}.'} for i in range(1,10)]
    legacy_overview=build_overview([],themes,lang)
    overview=build_overview([],themes,lang,detail_included=False)
    assert legacy in legacy_overview[0] and legacy not in ' '.join(overview)
    assert len(overview)==2 and label in overview[1] and reference in overview[1]
    for theme in themes:
        assert theme['summary_'+lang] in overview[0] or theme['title_'+lang] in overview[1]
    report=render_minutes([],'summary',lang,editorial=themes,
        executive_overview={lang:overview},respect_mode=True)
    assert legacy not in report and label in report

def test_summary_only_topic_inventory_is_bounded_and_explicit():
    themes=[{'sources':[REF],'title_es':f'Tema adicional {i:03d} '+'x'*55,
             'summary_es':f'Descripción única {i:03d}.'} for i in range(100)]
    overview=build_overview([],themes,'es',detail_included=False)
    assert len(overview)==2
    assert 'de 94 títulos adicionales' in overview[1]
    assert len(overview[1])<1200
    assert 'registro de evidencias' in overview[1]

def test_summary_only_no_additional_inventory_if_all_themes_sampled():
    overview=build_overview([],THEMES,'es',detail_included=False)
    assert overview==[THEMES[0]['summary_es']]

