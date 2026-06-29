from flowscope.presentation.gui.progress import ProgressReporter


def test_advance_normal():
    calls = []
    def on_update(current, total, label):
        calls.append((current, total, label))

    pr = ProgressReporter(on_update=on_update)
    pr.start_phase("Download", total=5, weight=1)

    pr.advance(1)
    pr.advance(1)

    assert pr._phase().current == 2
    assert len(calls) >= 2


def test_failures():
    calls = []
    def on_update(current, total, label):
        calls.append((current, total, label))

    pr = ProgressReporter(on_update=on_update)
    pr.start_phase("Download", total=5, weight=1)

    pr.fail(1, detail="Timeout")
    pr.advance(1)

    phase = pr._phase()
    assert phase.current == 2
    assert phase.failures == 1
    assert "falha" in calls[-1][2]


def test_multiple_phases_with_weights():
    phases_seen = []
    def on_update(current, total, label):
        phases_seen.append((current, total, label))

    pr = ProgressReporter(on_update=on_update)
    pr.start_phase("Portfolio", total=1, weight=1)
    pr.finish_phase()
    pr.start_phase("Download", total=2, weight=3)
    pr.advance(1)
    pr.finish_phase()
    pr.start_phase("Processing", total=4, weight=2)
    pr.advance(2)

    assert len(phases_seen) >= 3
    assert pr._completed_weight == 4  # 1 + 3


def test_phase_with_zero_total():
    calls = []
    def on_update(current, total, label):
        calls.append((current, total, label))

    pr = ProgressReporter(on_update=on_update)
    pr.start_phase("Empty", total=0, weight=1)
    pr.finish_phase()

    assert pr._completed_weight == 1


def test_throttle_skips_updates():
    call_count = 0
    def on_update(current, total, label):
        nonlocal call_count
        call_count += 1

    pr = ProgressReporter(on_update=on_update)
    pr._throttle_ms = 999999  # large throttle window
    pr.start_phase("Test", total=100, weight=1)

    for _ in range(50):
        pr.advance(1)

    assert call_count < 50  # throttled


def test_no_callback():
    pr = ProgressReporter(on_update=None)
    pr.start_phase("Test", total=10, weight=1)
    pr.advance(5)
    pr.fail(1)
    pr.finish_phase()

    assert pr._phase().current == 10
    assert pr._phase().failures == 1


def test_finish_phase_sets_current_to_total():
    pr = ProgressReporter()
    pr.start_phase("Test", total=10, weight=1)
    pr.advance(3)
    pr.finish_phase()

    assert pr._phase().current == 10


def test_label_includes_detail():
    calls = []
    def on_update(current, total, label):
        calls.append(label)

    pr = ProgressReporter(on_update=on_update)
    pr.start_phase("Download", total=5, weight=1)
    pr.advance(1, detail="2026-06-25")

    assert "2026-06-25" in calls[-1]
