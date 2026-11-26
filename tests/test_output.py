from engine.output import clock_srt, format_srt

def test_srt_timestamps():
    assert clock_srt(3661.239)=='01:01:01,239'
    assert format_srt([{'start':0.5,'end':1.2,'text':'Hola.'}]) == '1\n00:00:00,500 --> 00:00:01,200\nHola.\n\n'


def test_zip_groups_files_and_preserves_contents_on_reexport(tmp_path):
    from zipfile import ZipFile
    from engine.output import pack_result

    names = ('Minutas/RESUMEN_Y_MINUTA_LOCAL.md', 'Minutas/MINUTA_NO_GENERADA.txt',
             'Audio/parte_01.mp3', 'Audio/parte_02.m4a', 'Audio/parte_03.wav',
             'Transcripciones/transcripcion_parte_01.txt', 'Transcripciones/TRANSCRIPCION_SUBTITULOS.srt',
             'Datos_JSON/MINUTA_EVIDENCIAS.json', 'Datos_JSON/manifest.json',
             'Instrucciones/INSTRUCCIONES_CHATGPT_GEMINI.txt', 'Otros/extra.txt')
    for name in names:
        (tmp_path / name.split('/')[-1]).write_bytes(name.encode())
    (tmp_path / '.private.json').touch()
    (tmp_path / 'incomplete.partial').touch()
    target = tmp_path / 'RESULTADOS_COMPLETOS.zip'
    for _ in range(2):
        pack_result(tmp_path, target)
        with ZipFile(target) as archive:
            assert archive.testzip() is None
            root = 'RESULTADOS_COMPLETOS/'
            dirs = {root + name.split('/')[0] + '/' for name in names} | {root}
            assert {entry.filename for entry in archive.infolist() if entry.is_dir()} == dirs
            assert {entry.filename for entry in archive.infolist() if not entry.is_dir()} == {root + name for name in names}
            assert all(archive.read(root + name) == name.encode() for name in names)
    assert all((tmp_path / name.split('/')[-1]).read_bytes() == name.encode() for name in names)
