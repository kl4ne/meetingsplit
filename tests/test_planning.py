from engine.planning import plan_clips,choose_boundaries,assign_text_to_core
import pytest


def test_three_hour_coverage_without_gaps():
    clips=plan_clips(3*3600,[],target_seconds=600,max_seconds=675,overlap_seconds=12)
    assert clips[0].export_start==0
    assert clips[-1].core_end==10800
    assert all(a.core_end==b.core_start for a,b in zip(clips,clips[1:]))
    assert all(c.core_end-c.core_start<=675 for c in clips)
    assert all(c.export_start<=c.core_start and c.export_end>=c.core_end for c in clips)


def test_cut_near_pause():
    cuts=choose_boundaries(1400,[(591,594),(1190,1193)],target_seconds=600,max_seconds=690)
    assert 591<=cuts[1]<=594
    assert 1190<=cuts[2]<=1193


def test_boundary_timestamp_single_owner():
    assert assign_text_to_core(200,201,0,300)
    assert not assign_text_to_core(200,201,300,600)
    assert assign_text_to_core(300,300,300,600)
    assert not assign_text_to_core(300,300,0,300)


def test_invalid_ranges():
    with pytest.raises(ValueError): plan_clips(0,[])
    with pytest.raises(ValueError): plan_clips(600,[],overlap_seconds=100)


def test_only_last_short_core():
    clips=plan_clips(604,[],target_seconds=600,max_seconds=660)
    assert len(clips)==1
    assert clips[0].core_end==604
