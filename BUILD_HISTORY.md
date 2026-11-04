
### Phase 9 — QR Labels

**Commit:** 18da155

- `app/utils/qr.py` — generate_qr_png(data) → bytes
- `app/routes/equipment_label.py` — 3 routes (single, all, PNG)
- Self-contained templates for print (A6 single, A4 grid)
- 6 tests in tests/test_labels.py
- Suite: 95 passed, 3 skipped
