import pathlib
import run_pipeline


def test_pipeline_offline_creates_artifacts(tmp_path):
    res = run_pipeline.run(out_dir=str(tmp_path), send=True)  # send=True nhưng thiếu token -> dry-run
    html = pathlib.Path(res["html"]); docx = pathlib.Path(res["docx"])
    assert html.exists() and html.stat().st_size > 1000
    assert docx.exists() and docx.stat().st_size > 1000
    assert "PP" in res["telegram_text"] and "<a href=" in res["telegram_text"]
