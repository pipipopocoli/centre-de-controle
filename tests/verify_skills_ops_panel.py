"""
Verify Skills Ops Panel, Observability Badges, and Status Banner
(CP-0011, CP-0012, CP-0013, CP-0014)
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)


# ── CP-0011/0012: SkillsOpsPanel ──────────────────────────────────────────

def test_skills_ops_panel_instantiates():
    from app.ui.sidebar import SkillsOpsPanel
    panel = SkillsOpsPanel()
    assert panel is not None
    assert panel.objectName() == "skillsOpsPanel"
    print("[PASS] SkillsOpsPanel instantiates")


def test_set_skills():
    from app.ui.sidebar import SkillsOpsPanel
    panel = SkillsOpsPanel()
    panel.set_skills(["python", "ui", "mcp"])
    assert "python" in panel.skills_label.text()
    assert "ui" in panel.skills_label.text()
    print("[PASS] set_skills updates label")


def test_set_skills_empty():
    from app.ui.sidebar import SkillsOpsPanel
    panel = SkillsOpsPanel()
    panel.set_skills([])
    assert "-" in panel.skills_label.text()
    print("[PASS] set_skills empty shows dash")


def test_set_last_sync():
    from app.ui.sidebar import SkillsOpsPanel
    panel = SkillsOpsPanel()
    panel.set_last_sync("2026-02-13T14:00:00")
    assert "2026-02-13" in panel.last_sync_label.text()
    print("[PASS] set_last_sync updates label")


def test_set_profile_status():
    from app.ui.sidebar import SkillsOpsPanel
    panel = SkillsOpsPanel()
    panel.set_profile_status("loaded")
    assert "loaded" in panel.profile_label.text()
    print("[PASS] set_profile_status updates label")


def test_sync_state_idle():
    from app.ui.sidebar import SkillsOpsPanel
    panel = SkillsOpsPanel()
    panel.set_sync_state("idle")
    assert panel.sync_btn.text() == "Sync Now"
    assert panel.sync_btn.isEnabled()
    print("[PASS] set_sync_state idle")


def test_sync_state_loading():
    from app.ui.sidebar import SkillsOpsPanel
    panel = SkillsOpsPanel()
    panel.set_sync_state("loading")
    assert panel.sync_btn.text() == "Syncing..."
    assert not panel.sync_btn.isEnabled()
    print("[PASS] set_sync_state loading")


def test_sync_state_success():
    from app.ui.sidebar import SkillsOpsPanel
    panel = SkillsOpsPanel()
    panel.set_sync_state("success")
    assert "\u2713" in panel.sync_btn.text()
    print("[PASS] set_sync_state success")


def test_sync_state_error():
    from app.ui.sidebar import SkillsOpsPanel
    panel = SkillsOpsPanel()
    panel.set_sync_state("error")
    assert "\u2717" in panel.sync_btn.text()
    print("[PASS] set_sync_state error")


def test_set_sync_feedback():
    from app.ui.sidebar import SkillsOpsPanel
    panel = SkillsOpsPanel()
    panel.set_sync_feedback("Profile synced: 3 skills")
    assert "3 skills" in panel.sync_feedback.text()
    print("[PASS] set_sync_feedback updates label")


def test_sync_requested_signal():
    from app.ui.sidebar import SkillsOpsPanel
    panel = SkillsOpsPanel()
    signal_received = []
    panel.sync_requested.connect(lambda: signal_received.append(True))
    panel._on_sync_clicked()
    assert len(signal_received) == 1
    print("[PASS] sync_requested signal emitted on click")


# ── CP-0013: Observability Badges ─────────────────────────────────────────

def test_badge_instantiates():
    from app.ui.sidebar import ObservabilityBadge
    badge = ObservabilityBadge("Sync")
    assert badge.objectName() == "obsBadge"
    print("[PASS] ObservabilityBadge instantiates")


def test_badge_set_health_ok():
    from app.ui.sidebar import ObservabilityBadge
    badge = ObservabilityBadge("Test")
    badge.set_health("ok")
    assert badge._dot.property("health") == "ok"
    print("[PASS] badge set_health ok")


def test_badge_set_health_warn():
    from app.ui.sidebar import ObservabilityBadge
    badge = ObservabilityBadge("Test")
    badge.set_health("warn")
    assert badge._dot.property("health") == "warn"
    print("[PASS] badge set_health warn")


def test_badge_set_health_fail():
    from app.ui.sidebar import ObservabilityBadge
    badge = ObservabilityBadge("Test")
    badge.set_health("fail")
    assert badge._dot.property("health") == "fail"
    print("[PASS] badge set_health fail")


def test_badge_set_label():
    from app.ui.sidebar import ObservabilityBadge
    badge = ObservabilityBadge("Initial")
    badge.set_label("Updated")
    assert badge._text.text() == "Updated"
    print("[PASS] badge set_label")


def test_skills_panel_has_badges():
    from app.ui.sidebar import SkillsOpsPanel
    panel = SkillsOpsPanel()
    assert hasattr(panel, "badge_sync")
    assert hasattr(panel, "badge_memory")
    print("[PASS] SkillsOpsPanel has badge_sync and badge_memory")


# ── CP-0014: Status Banner ────────────────────────────────────────────────

def test_banner_instantiates_hidden():
    from app.ui.sidebar import StatusBanner
    banner = StatusBanner()
    assert banner.objectName() == "statusBanner"
    assert not banner.isVisible()
    print("[PASS] StatusBanner instantiates hidden")


def test_banner_show_warning():
    from app.ui.sidebar import StatusBanner
    banner = StatusBanner()
    banner.show_warning("Network degraded")
    assert banner.isVisible()
    assert "Network" in banner._message.text()
    assert banner.property("severity") == "warning"
    print("[PASS] show_warning makes banner visible")


def test_banner_show_error():
    from app.ui.sidebar import StatusBanner
    banner = StatusBanner()
    banner.show_error("Connection lost")
    assert banner.isVisible()
    assert banner.property("severity") == "error"
    print("[PASS] show_error sets severity to error")


def test_banner_dismiss():
    from app.ui.sidebar import StatusBanner
    banner = StatusBanner()
    banner.show_warning("Test")
    assert banner.isVisible()
    banner.dismiss()
    assert not banner.isVisible()
    print("[PASS] dismiss hides banner")


def test_sidebar_has_status_banner():
    from app.ui.sidebar import SidebarWidget
    sidebar = SidebarWidget(projects=["demo"])
    assert hasattr(sidebar, "status_banner")
    assert sidebar.status_banner.objectName() == "statusBanner"
    print("[PASS] SidebarWidget has status_banner")


def test_sidebar_has_skills_ops():
    from app.ui.sidebar import SidebarWidget
    sidebar = SidebarWidget(projects=["demo"])
    assert hasattr(sidebar, "skills_ops")
    assert sidebar.skills_ops.objectName() == "skillsOpsPanel"
    print("[PASS] SidebarWidget has skills_ops attribute")


if __name__ == "__main__":
    tests = [
        # CP-0011/0012
        test_skills_ops_panel_instantiates,
        test_set_skills,
        test_set_skills_empty,
        test_set_last_sync,
        test_set_profile_status,
        test_sync_state_idle,
        test_sync_state_loading,
        test_sync_state_success,
        test_sync_state_error,
        test_set_sync_feedback,
        test_sync_requested_signal,
        # CP-0013
        test_badge_instantiates,
        test_badge_set_health_ok,
        test_badge_set_health_warn,
        test_badge_set_health_fail,
        test_badge_set_label,
        test_skills_panel_has_badges,
        # CP-0014
        test_banner_instantiates_hidden,
        test_banner_show_warning,
        test_banner_show_error,
        test_banner_dismiss,
        test_sidebar_has_status_banner,
        test_sidebar_has_skills_ops,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {t.__name__}: {e}")
            failed += 1

    print(f"\n--- Results: {passed} passed, {failed} failed ---")
    if failed:
        sys.exit(1)
