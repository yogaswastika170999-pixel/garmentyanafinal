# plan.md — Fix PO Accessories Flow + Dashboard/Serial UX

## 1) Objectives
- Fix **core workflow correctness**: PO accessories saved in `po_accessories` must be visible and usable across **PO detail → shipment creation/detail → vendor portal**.
- Ensure **data linkage is reliable** (shipment-level `po_id` where applicable; consistent accessor loading by `po_id`).
- Deliver targeted **UI/UX improvements**:
  - Dashboard: clearer KPIs, non-blank charts, better layout + date filtering.
  - Serial Tracking: improved timeline readability + key metrics surfaced.

---

## 2) Implementation Steps (Phased)

### Phase 1 — Core POC: Accessories Data Propagation (Isolation)
**Goal:** Prove the core data flow works via API-only tests before touching broad UI.

1) **Add POC test script** `tests/poc_po_accessories_flow.py`
   - Seed minimal data: vendor, buyer, 1 product+variant, 1 PO with 1 item.
   - Create 2 accessories + attach to PO via `POST /api/po-accessories`.
   - Assert:
     - `GET /api/production-pos/{po_id}` returns `po_accessories[]`.
     - `GET /api/po-accessories?po_id=...` returns same items.
     - Create vendor shipment referencing that PO.
     - `GET /api/vendor-shipments/{sid}` returns `po_accessories_by_po` (or equivalent) and includes accessories for the linked PO(s).

2) **Backend patches until POC is green**
   - `GET /api/production-pos/{po_id}`: include `po_accessories` in response.
   - `GET /api/production-pos` list: include `po_accessories_count` (and optionally a small preview array).
   - `POST /api/vendor-shipments`: set shipment-level `po_id`/`po_number` when items contain a single PO (or store `po_ids: []` if multi-PO); keep backward compatibility.
   - `GET /api/vendor-shipments/{sid}`: include PO-linked accessories in response (grouped by `po_id`).

**Phase 1 user stories**
1. As an admin, I can fetch a PO and see its accessories in the same response payload.
2. As an admin, I can fetch PO accessories by `po_id` and get the exact items I added.
3. As an admin, I can create a vendor shipment and the API links it to the PO for downstream reads.
4. As an admin, when I open vendor shipment detail via API, I can see accessories grouped by PO.
5. As a developer, I can run the POC script and get deterministic PASS/FAIL for the accessories flow.

---

### Phase 2 — V1 App Development: ERP + Vendor Portal UI Wiring
**Goal:** Build the UI around the proven core flow.

1) **ERP — ProductionPOModule.jsx**
   - In PO Detail modal: render an “Aksesoris” section (table with name/code/qty/unit/notes).
   - In PO list rows: display accessories count chip.

2) **ERP — VendorShipmentModule.jsx**
   - When selecting a PO in “Load Item dari PO”:
     - Fetch `/api/po-accessories?po_id=...` and show a side panel/table “Aksesoris dari PO”.
     - (MVP) informational display only (do not mix with material items).
   - Shipment Detail modal:
     - Show “Aksesoris terkait PO” section (based on new shipment detail fields).

3) **Vendor Portal — VendorPortalApp.jsx**
   - In shipment detail view for vendor: display the same “Aksesoris terkait PO” section.

4) **Incremental testing (manual + scripted)**
   - Create PO with accessories → open PO detail → verify display.
   - Create shipment selecting PO → verify accessories show while creating.
   - Open shipment detail (ERP + vendor) → verify accessories displayed consistently.

**Phase 2 user stories**
1. As an admin, when I open PO detail, I can clearly see accessories and their required quantities.
2. As an admin, when I pick a PO while creating a shipment, I can see the PO’s accessories immediately.
3. As an admin, when I open shipment detail, I can see accessories related to that shipment’s PO.
4. As a vendor, when I open shipment detail in the vendor portal, I can see the PO accessories needed for production.
5. As an admin, I can verify accessories visibility without exporting or using separate modules.

---

### Phase 3 — UX Improvements: Dashboard + Serial Tracking
**Goal:** Improve usability without changing business logic.

1) **Dashboard**
   - Compact KPI grid + consistent spacing.
   - Fix any blank charts by aligning with existing backend data sources.
   - Add date range filter (week/month/custom) applied to KPIs/charts.

2) **Serial Tracking**
   - Improve timeline layout (group events, show quantities + shipment numbers).
   - Surface key computed fields prominently (ordered/shipped/received/remaining).

**Phase 3 user stories**
1. As an admin, I can quickly understand today’s operational status from a clean dashboard.
2. As an admin, I can filter dashboard analytics by date range and see charts update.
3. As an admin, I can click into serial tracking and immediately see remaining qty and current status.
4. As an admin, I can read a serial timeline that clearly connects PO → shipments → inspections.
5. As an operations user, I can spot problems faster because charts and timelines are not cluttered.

---

### Phase 4 — Regression Testing + Hardening
1) Add/extend pytest coverage for:
   - PO create + accessories attach + PO detail.
   - Vendor shipment detail includes grouped accessories.
2) Run one full end-to-end regression pass across PO → shipment → vendor portal views.
3) Fix any breakages found before moving to new features.

---

## 3) Next Actions
1) Implement `tests/poc_po_accessories_flow.py` and run it.
2) Patch backend responses/linking:
   - `GET /production-pos/{id}` include `po_accessories`.
   - `GET /production-pos` include `po_accessories_count`.
   - Shipment create/detail include PO-linked accessories.
3) Wire frontend display in PO detail + shipment create/detail + vendor portal shipment detail.
4) Run a regression sweep (PO → shipment → vendor portal) and stabilize.

---

## 4) Success Criteria
- Accessories added to a PO are visible in:
  - PO detail (ERP)
  - Vendor shipment creation (ERP)
  - Vendor shipment detail (ERP)
  - Vendor portal shipment detail
- Backend APIs provide consistent, PO-linked accessories payloads with minimal extra calls.
- Dashboard and Serial Tracking screens are noticeably clearer, with working filters/charts/timeline.
- POC script passes and regression tests confirm no breakage in core PO/shipment flows.
