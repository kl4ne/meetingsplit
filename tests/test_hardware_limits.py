from engine.planning import plan_clips


def test_export_size_limit_with_overlap_for_three_hour_meeting():
    duration = 3 * 3600
    for limit_minutes in (5, 10, 15, 20):
        for overlap in (10, 20, 30):
            max_total = limit_minutes * 60
            max_core = max_total - 2 * overlap
            clips = plan_clips(duration, [], target_seconds=max_core - 30,
                               max_seconds=max_core, overlap_seconds=overlap)
            assert clips[0].export_start == 0
            assert clips[-1].core_end == duration
            assert all(c.export_end - c.export_start <= max_total + 0.01 for c in clips)
            assert all(a.core_end == b.core_start for a,b in zip(clips,clips[1:]))


def test_export_limit_with_silence_candidates():
    silences=[(x-4.0, x+4.0) for x in range(220, 10800, 230)]
    clips=plan_clips(10800,silences,target_seconds=230,max_seconds=260,
                     overlap_seconds=20)
    assert max(x.export_end-x.export_start for x in clips) <= 300.01
