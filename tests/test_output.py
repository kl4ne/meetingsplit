from engine.output import clock_srt, format_srt

def test_srt_timestamps():
    assert clock_srt(3661.239)=='01:01:01,239'
    assert format_srt([{'start':0.5,'end':1.2,'text':'Hola.'}]) == '1\n00:00:00,500 --> 00:00:01,200\nHola.\n\n'
