from analytics import build_analysis
from report import render


def test_view_model_shape():
    data = build_analysis.run()
    v = render.build_view(data)
    assert any(c["key"] == "pp" for c in v["kpi"])
    pp_card = [c for c in v["kpi"] if c["key"] == "pp"][0]
    assert pp_card["date"] and pp_card["fresh"]["emoji"] in ("🟢", "🟡", "🔴")
    pp = v["atsight"]["pp"]
    assert sum(1 for r in pp["rows"] if r["is_best"]) == 1
    ats = [r["at_sight_equiv"] for r in pp["rows"]]
    assert ats == sorted(ats)
    assert "label" in pp["rows"][0] and "date" in pp["rows"][0]
    assert v["sources"] and any(s["url"] for s in v["sources"])
    assert v["news"] and v["narrative"]["picture"] and v["alerts"]
    assert v["glossary"] and v["forecast"].get("pp")


def test_glossary_static():
    v = render.build_view(build_analysis.run())
    terms = {g["term"] for g in v["glossary"]}
    assert "At-sight tương đương" in terms and "Theil's U" in terms
