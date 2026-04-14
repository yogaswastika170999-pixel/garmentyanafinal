# plan.md — Accessories Flow Fix (Completed) + Dashboard/Serial UX (Next)

## 1) Objectives
### Completed
- Fix **core workflow correctness**: PO accessories saved in `po_accessories` are now visible across:
  - **PO detail (ERP)**
  - **Vendor shipment creation (ERP)**
  - **Vendor shipment detail (ERP)**
  - **Vendor portal shipment view**
- Ensure **data linkage is reliable**:
  - Vendor shipments now store shipment-level `po_id` / `po_number` when items reference a single PO.
  - Shipment detail aggregates PO accessories from linked `po_id` sources.

### Current (Next)
- Deliver targeted **UI/UX improvements**:
  - Dashboard: clearer KPIs, non-blank charts, better layout + date filtering.
  - Serial Tracking: improved timeline readability + key metrics (ordered/shipped/received/remaining) surfaced.
- Prepare for **new features discussion** after UX improvements and/or stabilization.

---

## 2) Implementation Steps (Phased)

### Phase 1 — Core POC: Accessories Data Propagation (Isolation) ✅ COMPLETE
**Goal:** Prove the core data flow works via API-only tests before touching broad UI.

1) **POC test script** `tests/poc_po_accessories_flow.py` ✅
   - Seeds minimal data: vendor, product+variant, PO with 1 item.
   - Creates 2 accessories + attaches to PO via `POST /api/po-accessories`.
   - Asserts:
     - `GET /api/production-pos/{po_id}` returns `po_accessories[]`.
     - `GET /api/po-accessories?po_id=...` returns same items.
     - Create vendor shipment referencing that PO.
     - `GET /api/vendor-shipments/{sid}` returns `po_accessories[]` populated for linked PO(s).
   - Result: **23 passed / 0 failed**.

2) **Backend patches** ✅
   - `GET /api/production-pos/{po_id}`: include `po_accessories`.
   - `GET /api/production-pos` list: include `po_accessories` and `po_accessories_count`.
   - `POST /api/vendor-shipments`:
     - Derive and store shipment-level `po_id` / `po_number` when items reference a single PO.
   - `GET /api/vendor-shipments/{sid}`: include `po_accessories` aggregated from linked PO(s).
   - `GET /api/vendor-shipments` list: include `po_accessories_count`.

**Phase 1 user stories (met)**
1. Admin can fetch a PO and see accessories in the same response payload.
2. Admin can fetch PO accessories by `po_id`.
3. Admin can create vendor shipment and API links it to PO.
4. Admin can open shipment detail and see PO accessories.
5. Developer can run POC and get deterministic PASS/FAIL.

---

### Phase 2 — V1 App Development: ERP + Vendor Portal UI Wiring ✅ COMPLETE
**Goal:** Build UI around the proven core flow.

1) **ERP — ProductionPOModule.jsx** ✅
   - PO Detail modal now renders an “Aksesoris PO” section (name/code/qty/unit/notes).

2) **ERP — VendorShipmentModule.jsx** ✅
   - When selecting a PO in “Load Item dari PO”:
     - Fetches `/api/po-accessories?po_id=...`.
     - Displays “Aksesoris dari PO” panel (informational; not mixed with shipment material items).
   - Shipment Detail modal:
     - Displays “Aksesoris terkait PO” section using shipment detail payload.
   - UX small fix:
     - Clearing PO selection also clears accessories panel.

3) **Vendor Portal — VendorPortalApp.jsx** ✅
   - Shipment cards show a toggle panel “Aksesoris PO (N item)” which lazy-loads shipment detail and renders the accessory list.

4) **Verification** ✅
   - POC test script: green.
   - Testing agent: **100% success** across tested accessories scenarios.

**Phase 2 user stories (met)**
1. Admin sees accessories in PO detail.
2. Admin sees PO accessories while preparing vendor shipment.
3. Admin sees accessories in vendor shipment detail.
4. Vendor sees PO accessories from their shipment view.
5. Accessories visibility can be verified without exports or separate modules.

---

### Phase 3 — UX Improvements: Dashboard + Serial Tracking (Pending)
**Goal:** Improve usability without changing business logic.

#### 3.1 Dashboard
- **UI/UX cleanup**
  - Compact KPI grid + consistent spacing.
  - Make KPI cards consistently clickable (optional) to drill-down lists.
- **Fix blank/incorrect charts** (align frontend queries with backend sources)
  - Confirm “Status Work Order” chart sources.
  - Confirm “Top Garment by Production” aggregation.
- **Date range filtering**
  - Week / Month / Custom range.
  - Applies to KPIs + charts.

#### 3.2 Serial Tracking
- **Timeline readability**
  - Group events (PO → shipments → inspections → jobs → dispatch/returns).
  - Show shipment numbers, quantities, and dates in a predictable layout.
- **Key metrics surfaced**
  - Ordered, shipped, received, remaining.
  - Ensure remaining is computed from ordered - shipped (not production output).

**Phase 3 user stories (target)**
1. Admin quickly understands operational status from a clean dashboard.
2. Admin can filter dashboard analytics by date range.
3. Admin can open serial tracking and see remaining qty + current status immediately.
4. Admin can read a serial timeline that clearly connects lifecycle events.
5. Ops can spot bottlenecks faster due to clearer charts/timeline.

---

### Phase 4 — Regression Testing + Hardening (Next after Phase 3)
1) Extend automated coverage:
   - Keep `tests/poc_po_accessories_flow.py` as a regression gate.
   - Add UI regression checks for dashboard filter and serial tracking timeline (lightweight).
2) Run full end-to-end regression pass:
   - PO → vendor shipment → vendor portal views.
   - Dashboard and serial tracking after UX updates.
3) Fix any breakages before starting new feature work.

---

## 3) Next Actions
1) Confirm scope for **Phase 3**:
   - Which dashboard charts/KPIs are highest priority?
   - Which serial tracking pain points matter most (timeline vs computations vs search)?
2) Implement dashboard date filter + chart fixes.
3) Implement serial tracking UI layout improvements + metric surfacing.
4) Run a regression sweep (accessories flow + updated dashboard + serial tracking).

---

## 4) Success Criteria
### Already achieved
- Accessories added to a PO are visible in:
  - PO detail (ERP)
  - Vendor shipment creation (ERP)
  - Vendor shipment detail (ERP)
  - Vendor portal shipment view
- Backend provides consistent PO-linked accessories payloads.
- POC script passes (**23/23**).
- Testing agent verified **100% success** for the accessories fix.

### Remaining
- Dashboard is compact, non-blank, and filterable by date.
- Serial tracking is easier to read and shows key metrics clearly.
- Regression checks pass after Phase 3 changes.
