import os

from docx import Document

from app.data_source import MockDataSource
from app.indicators import compute_indicators
from app.models import RunResult
from app.report import build_report


def test_build_report_creates_valid_docx(tmp_path):
    snap = MockDataSource().fetch("NVL", 40)
    ind = compute_indicators(snap)
    result = RunResult(
        ticker="NVL",
        snapshot=snap,
        indicators=ind,
        analysis="Đoạn 1 phân tích.\n\nĐoạn 2 phân tích.",
        summary="Tóm tắt NVL",
        ai_used=False,
    )
    path = build_report(result, str(tmp_path))
    assert os.path.isfile(path)
    assert path.endswith(".docx")

    # Mở lại file để chắc chắn DOCX hợp lệ và có tiêu đề.
    doc = Document(path)
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "NVL" in text
    assert "phân tích" in text.lower()
