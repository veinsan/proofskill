# Report and deck sync (Deliverable 3)

Two Google Apps Script files that bring the team's Google Doc report and Google Slides deck in line with the deployed website and add the Deliverable 3 content. They run from a standalone Apps Script project as the document owner.

| File | Target | Entry points |
| --- | --- | --- |
| `report.gs` | Report `1FcvZa_igEO7X7qGzuZQ7sMiDCbvlj-YDIaBueJL-aSg`, tab `Final` | `dryRun()` counts every find without changing anything; `applyAll()` applies the text replacements, table edits, the new Gambar 10.1, Catatan Revisi, Tabel 0.3 and 0.5, the new Bab XI (Prototipe dan Pengujian), Bab XII (Penutup), and the Lampiran |
| `slides.gs` | Deck `1WfNM9kEujELB3kGDd93bluzXbP0uFayLdAguLaKmoZk` | `slidesDryRun()` and `slidesApplyAll()`: text and table fixes, plus the Deliverable 3 section before Kesimpulan |

Images load from `raw.githubusercontent.com` on the `docs/d3-report-sync` branch: `docs/evidence/ui/` (full-page screenshots of the deployed site), `docs/figures/arsitektur-deployed.png` (the new Gambar 10.1), and `docs/figures/slides/` (crops for the deck). Run each `apply` function once; to undo, restore the earlier version from File > Version history. After the report run, refresh the table of contents in the document.
