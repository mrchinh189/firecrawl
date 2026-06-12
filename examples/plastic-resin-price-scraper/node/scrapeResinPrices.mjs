/**
 * Cao gia nguyen vat lieu nhua nguyen sinh PP / PE bang Firecrawl Cloud (Node.js).
 *
 * Cach dung:
 *   export FIRECRAWL_API_KEY=fc-...
 *   npm install
 *   npm start
 *
 * Ket qua ghi ra thu muc ../output/ duoi dang JSON + CSV.
 * Cau hinh nguon va schema o file ../sources.json.
 */

import { readFile, mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import Firecrawl from "@mendable/firecrawl-js";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");
const CONFIG_PATH = resolve(ROOT, "sources.json");
const OUTPUT_DIR = resolve(ROOT, "output");

const CSV_FIELDS = [
  "source",
  "material",
  "grade",
  "price",
  "currency",
  "unit",
  "region",
  "date",
  "change",
  "scraped_at",
];

function fail(msg) {
  console.error(msg);
  process.exit(1);
}

async function loadConfig() {
  try {
    return JSON.parse(await readFile(CONFIG_PATH, "utf-8"));
  } catch (err) {
    fail(`Khong doc duoc cau hinh ${CONFIG_PATH}: ${err.message}`);
  }
}

function buildClient() {
  const apiKey = process.env.FIRECRAWL_API_KEY;
  if (!apiKey) {
    fail(
      "Thieu FIRECRAWL_API_KEY. Lay key tai https://firecrawl.dev roi:\n" +
        "    export FIRECRAWL_API_KEY=fc-...",
    );
  }
  return new Firecrawl({ apiKey });
}

async function scrapeSource(client, source, schema, scrapeCfg) {
  const { name, url } = source;
  console.log(`  -> [${name}] dang scrape: ${url}`);

  const jsonFormat = { type: "json", schema };
  if (source.prompt) jsonFormat.prompt = source.prompt;

  let doc;
  try {
    doc = await client.scrape(url, {
      formats: [jsonFormat],
      onlyMainContent: scrapeCfg.onlyMainContent ?? true,
      timeout: scrapeCfg.timeoutMs ?? 60000,
      maxAge: scrapeCfg.maxAgeMs ?? 3600000,
    });
  } catch (err) {
    console.log(`     [LOI] ${name}: ${err.message}`);
    return [];
  }

  const data = doc?.json ?? {};
  const prices = Array.isArray(data.prices) ? data.prices : [];
  const scrapedAt = new Date().toISOString();

  const rows = prices
    .filter((p) => p && typeof p === "object")
    .map((p) => ({
      source: name,
      material: p.material ?? source.material ?? "",
      grade: p.grade ?? "",
      price: p.price ?? "",
      currency: p.currency ?? "",
      unit: p.unit ?? "",
      region: p.region ?? "",
      date: p.date ?? "",
      change: p.change ?? "",
      scraped_at: scrapedAt,
    }));

  console.log(`     OK: ${rows.length} dong gia`);
  return rows;
}

function toCsv(rows) {
  const escape = (v) => {
    const s = String(v ?? "");
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const header = CSV_FIELDS.join(",");
  const lines = rows.map((r) => CSV_FIELDS.map((f) => escape(r[f])).join(","));
  return [header, ...lines].join("\n");
}

async function writeOutputs(rows) {
  await mkdir(OUTPUT_DIR, { recursive: true });
  const stamp = new Date()
    .toISOString()
    .replace(/[:T]/g, "")
    .replace(/\..+/, "")
    .replace(/-/g, "");
  const jsonPath = resolve(OUTPUT_DIR, `resin_prices_${stamp}.json`);
  const csvPath = resolve(OUTPUT_DIR, `resin_prices_${stamp}.csv`);

  await writeFile(jsonPath, JSON.stringify(rows, null, 2), "utf-8");
  await writeFile(csvPath, toCsv(rows), "utf-8");

  console.log(`\nDa ghi ${rows.length} dong gia vao:`);
  console.log(`  - ${jsonPath}`);
  console.log(`  - ${csvPath}`);
}

async function main() {
  const cfg = await loadConfig();
  const client = buildClient();
  const schema = cfg.schema;
  const scrapeCfg = cfg.scrape ?? {};
  const sources = (cfg.sources ?? []).filter((s) => s.enabled);

  if (sources.length === 0) {
    fail("Khong co nguon nao duoc bat (enabled=true) trong sources.json");
  }

  console.log(`Bat dau cao gia tu ${sources.length} nguon...\n`);
  const allRows = [];
  for (const source of sources) {
    allRows.push(...(await scrapeSource(client, source, schema, scrapeCfg)));
  }

  if (allRows.length === 0) {
    console.log("\nKhong trich xuat duoc dong gia nao. Kiem tra lai URL / prompt / schema.");
    return;
  }

  await writeOutputs(allRows);
}

main().catch((err) => fail(err.stack || String(err)));
