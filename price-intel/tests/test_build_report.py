from report import build_report


def test_build_report_html_has_sections(tmp_path):
    out = tmp_path / "report.html"
    build_report.build(out_path=str(out))
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    for marker in ["Tổng quan", "Phân tích", "at-sight", "khu vực",
                   "Cảnh báo", "Dự báo", "Nguồn", "Thuật ngữ", "Tin tức"]:
        assert marker in text, f"thiếu mục: {marker}"
    assert 'href="http' in text
    assert "2026-06-" in text
    assert ("🟢" in text or "🟡" in text or "🔴" in text)
    assert "best" in text
