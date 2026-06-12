"""Mot lan thu thap gia: scrape -> normalize -> ghi DB -> canh bao."""
import logging

import alert
import config
import db
import firecrawl_client as fc
import normalize

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("run")


def run_once() -> int:
    cfg = config.load_sources_config()
    schema = cfg["schema"]
    scrape_cfg = cfg.get("scrape", {})
    sources = [s for s in cfg["sources"] if s.get("enabled", False)]

    db.sync_sources(cfg["sources"])
    run_id = db.start_run()
    total_added = 0
    errors: list[str] = []

    log.info("Bat dau thu thap tu %d nguon", len(sources))
    for source in sources:
        name = source["name"]
        try:
            raw_rows = fc.scrape_source(source, schema, scrape_cfg)
            log.info("[%s] %d dong tho", name, len(raw_rows))
            for raw in raw_rows:
                row = normalize.normalize_row(raw, source.get("material", "OTHER"))
                if not row:
                    continue
                previous = db.get_previous_price(
                    name, row["material"], row["grade"], row["region"]
                )
                inserted = db.upsert_price(name, row)
                if inserted:
                    total_added += 1
                alert.check_and_alert(name, row, previous)
        except Exception as exc:  # noqa: BLE001
            log.exception("[%s] loi: %s", name, exc)
            errors.append(f"{name}: {exc}")

    status = "success" if not errors else ("partial" if total_added else "failed")
    db.finish_run(run_id, status, total_added, "; ".join(errors))
    log.info("Hoan tat: them %d dong, status=%s", total_added, status)

    if errors:
        alert.send_telegram(
            f"⚠️ Thu thap gia co loi ({len(errors)} nguon):\n" + "\n".join(errors[:10])
        )
    return total_added


if __name__ == "__main__":
    run_once()
