# plan.md — Accessories Flow Fix ✅ + RBAC Fix ✅ + Inspection+Accessories ✅ + PDFs ✅ + Product Photos ✅ + Analytics ✅ + Serial Tracking ✅ + Stabilization/Docs ✅

## 1) Objectives

### Completed
- Fix **PO accessories propagation** so accessories created during PO creation are visible in:
  - **PO detail (ERP)**
  - **Vendor shipment creation (ERP)**
  - **Vendor shipment detail (ERP)**
  - **Vendor portal shipment view**
- Improve **data linkage** for vendor shipments:
  - Vendor shipments store shipment-level `po_id` / `po_number` when items reference a single PO.
  - Vendor shipment detail aggregates `po_accessories` from linked PO(s).
- Extend **Material Inspection** to include **Accessories Inspection**:
  - Vendor inspects both materials and accessories in one inspection payload (`items` + `accessory_items`).
  - Inspection listing/detail returns both material items and accessories separately.
  - Fix: inspection creation can **infer `vendor_id` from shipment** when not explicitly provided.
- Fix **RBAC / Custom Role** enforcement so feature access matches Role Management settings:
  - Backend: `require_auth` async and preloads permissions; custom roles can operate per permission.
  - Frontend: replace hardcoded `isSuperAdmin` checks with `hasPerm` model for create buttons.
- Add **Vendor Inspection PDF export** (materials + accessories) with detailed context.
- Add **Product Photos** in product master:
  - Upload photo via `POST /api/products/{id}/photo`.
  - Display photo column + preview.
  - Hotfix: initialize `photo_url` on product creation (so API always returns a consistent schema).
- Upgrade **Dashboard UI/UX + Analytics**:
  - KPI redesign + drilldowns.
  - Date range filtering via `GET /api/dashboard/analytics?from&to`.
- Upgrade **Serial Tracking**:
  - Add `GET /api/serial-list` endpoint.
  - ERP UI: list + expand + trace timeline.
- **Per-dispatch PDF export** for Buyer Shipment:
  - Export PDF per dispatch row (not a combined shipment-only PDF).
- **Auto-create material request** for missing accessories on vendor inspection:
  - Hotfix: align inserted `material_requests` schema with manual request fields (`original_shipment_id`, `requested_qty`, totals).
- **Hotfix (critical): Frontend compile error**
  - Fixed JSX fragment mismatch in `ProductionPOModule.jsx` (missing `<>...</>` around action buttons).
  - Verified `yarn build` succeeds (warnings only).
- **Documentation delivered**
  - Created `/app/DESIGN_TECHNICAL_DOCUMENT.md` with complete architecture + DB + API + feature documentation.

### Current (Now)
- System scope for requested v8.0 items is **complete**.
- Remaining (optional, future): session longevity improvements, backend modularization (split `server.py` into routers), pagination, realtime events.

---

## 2) Implementation Steps (Phased)

### Phase 1 — Accessories Data Propagation (Isolation) ✅ COMPLETE
**Goal:** Prove PO accessories flow works via API tests and patch backend until green.

1) **POC test script** `tests/poc_po_accessories_flow.py` ✅
   - Seeds vendor/product/variant/PO.
   - Creates accessories and attaches to PO.
   - Asserts PO detail + shipment detail include `po_accessories`.
   - Result: **23 passed / 0 failed**.

2) **Backend patches** ✅
   - `GET /api/production-pos/{po_id}` includes `po_accessories`.
   - `GET /api/production-pos` includes `po_accessories` + `po_accessories_count`.
   - `POST /api/vendor-shipments` stores `po_id`/`po_number` at shipment level when single PO.
   - `GET /api/vendor-shipments/{sid}` includes `po_accessories` aggregated by linked PO(s).
   - `GET /api/vendor-shipments` includes `po_accessories_count`.

**Phase 1 user stories (met)**
1. Admin can fetch a PO and see accessories.
2. Admin can fetch PO accessories by `po_id`.
3. Admin can create shipment linked to PO.
4. Admin can view shipment detail and see accessories.

---

### Phase 2 — ERP + Vendor Portal UI Wiring ✅ COMPLETE
**Goal:** Show PO accessories in ERP and Vendor Portal flows.

1) **ERP — ProductionPOModule.jsx** ✅
   - PO detail modal shows “Aksesoris PO”.

2) **ERP — VendorShipmentModule.jsx** ✅
   - Selecting PO in shipment creation loads and displays “Aksesoris dari PO”.
   - Shipment detail modal shows “Aksesoris terkait PO”.

3) **Vendor Portal — VendorPortalApp.jsx** ✅
   - Shipment cards show expandable “Aksesoris PO” panel (lazy-load shipment detail).

4) **Verification** ✅
   - Testing agent: **100% success** for the accessories visibility flow.

**Phase 2 user stories (met)**
1. Admin sees accessories in PO detail.
2. Admin sees PO accessories when preparing shipment.
3. Vendor sees PO accessories in portal.

---

### Phase 3 — Critical Bug Fix: RBAC / Custom Role Enforcement ✅ COMPLETE
**Goal:** Ensure users with custom roles can do exactly what permissions allow.

#### 3.1 Diagnose current RBAC model ✅
- Root cause: legacy `check_role` only compared role names and ignored custom role permission mappings.

#### 3.2 Implement consistent permission checking ✅
- Backend RBAC:
  - `require_auth` became async and preloads permissions into `user['_permissions']`.
  - `check_role` updated to allow custom roles based on loaded permission keys.
  - Updated route modules to `await require_auth`.
- Frontend:
  - Replace `isSuperAdmin` checks with `hasPerm(userPermissions, 'permission.key')`.

#### 3.3 Add RBAC regression tests ✅
- Added `tests/poc_rbac_custom_role.py`:
  - Create role with all permissions.
  - Create user assigned to that role.
  - Assert user can create PO and create shipment.

#### 3.4 UI verification ✅
- Iteration 3 confirmed:
  - Custom role user can login.
  - “Buat PO” and “Buat Shipment” buttons visible and clickable when permissions allow.

---

### Phase 4 — Material + Accessories Inspection & Requests ✅ COMPLETE
**Goal:** Vendor can inspect materials + accessories; system auto-creates requests when accessories are missing.

#### 4.1 Data model additions/updates ✅
- Added accessories as a second line group:
  - `vendor_material_inspection_items.item_type` = `material` | `accessory`
  - Inspection header includes `total_acc_received`, `total_acc_missing`.

#### 4.2 API changes ✅
- `POST /api/vendor-material-inspections` supports:
  - `items[]` (materials)
  - `accessory_items[]` (accessories)
- `GET /api/vendor-material-inspections` returns:
  - `items[]` + `accessory_items[]`
- Hardening fix:
  - Inspection POST can infer `vendor_id` from shipment if not provided.

#### 4.3 Auto-create material requests for missing accessories ✅
- Implemented auto-insert into `material_requests` when `missing_qty > 0` on accessory items.
- Hotfix after iteration 3:
  - Align schema with manual material request fields:
    - `original_shipment_id` + `original_shipment_number`
    - `items[].requested_qty` (instead of `missing_qty`)
    - `total_requested_qty`

#### 4.4 UI changes ✅
- Vendor portal inspection form includes accessories inspection table.
- Inspection detail modal includes accessories result.

---

### Phase 5 — Vendor Inspection PDF Export (Materials + Accessories) ✅ COMPLETE
**Goal:** Vendor can export PDF of inspection containing detailed PO & item info.

- Backend: `GET /api/export-pdf?type=vendor-inspection&id={inspection_id}`.
- Frontend: Vendor portal inspection detail includes authenticated **PDF Export** button.

---

### Phase 6 — Product Photos (Master Data + Propagation) ✅ COMPLETE
**Goal:** Upload and display product photos across system.

#### 6.1 Backend ✅
- `POST /api/products/{id}/photo` uploads and stores a `photo_url`.
- Hotfix after iteration 3:
  - Ensure `photo_url` initialized on product creation (`POST /api/products`).

#### 6.2 Frontend ✅
- Products module: photo column + upload + preview.

#### 6.3 Verification ✅
- Iteration 3 confirmed photo upload UI present and functional.

---

### Phase 7 — Dashboard UI/UX + Analytics Expansion ✅ COMPLETE
**Goal:** More modern and informative analytics with date range filters.

- Endpoint: `GET /api/dashboard/analytics?from=YYYY-MM-DD&to=YYYY-MM-DD`.
- UI: KPI grid, alert bar, drilldowns, charts.
- Iteration 3 verified date filter changes analytics output.

---

### Phase 8 — Serial Tracking Improvements (ERP + Vendor Portal readiness) ✅ COMPLETE
**Goal:** Expandable serial list with “ongoing serials” view.

- Backend: `GET /api/serial-list` with filters.
- ERP UI: list + expandable mini timeline + trace timeline.
- Iteration 3 verified endpoint + UI tabs/search.

---

### Phase 9 — Regression Testing + Hardening ✅ COMPLETE
**Goal:** Ensure latest batch is fully verified end-to-end after recent changes.

#### 9.1 Test iterations ✅
- Iteration 1: accessories flow ✅
- Iteration 2: new features mostly ✅ (vendor_id inference later fixed)
- Iteration 3: comprehensive ✅
  - Found 2 medium issues:
    1) `photo_url` not initialized for new products
    2) auto-created material request schema mismatch vs manual requests
  - Both issues fixed ✅

#### 9.2 Evidence
- Test reports:
  - `/app/test_reports/iteration_1.json`
  - `/app/test_reports/iteration_2.json`
  - `/app/test_reports/iteration_3.json`

---

### Phase 10 — Documentation ✅ COMPLETE
**Goal:** Fulfill user request to update technical documentation.

#### 10.1 Delivered ✅
- Created `/app/DESIGN_TECHNICAL_DOCUMENT.md` including:
  - Architecture overview (3 portals, RBAC, JWT)
  - Key collections and relationships (PO ↔ accessories ↔ shipment ↔ inspection)
  - New endpoints:
    - `/api/dashboard/analytics`
    - `/api/serial-list`
    - `/api/products/{id}/photo`
    - per-dispatch PDF export (`type=buyer-dispatch`)
    - updated `/api/vendor-material-inspections` (accessories + auto-requests)
  - Storage notes (`EMERGENT_LLM_KEY` optional)
  - Testing references and checklists

---

## 3) Next Actions

### P0 (Done)
- ✅ Comprehensive testing executed and issues fixed.
- ✅ Technical documentation created.

### P1 (Optional / Future)
1) **Session stability improvements**
   - Consider refresh token / keep-alive / longer TTL.
2) **Backend modularization**
   - Split monolithic `/app/backend/server.py` into domain routers under `/app/backend/routes/`.
3) **Server-side pagination**
   - For large lists (PO, shipments, jobs, logs).
4) **Real-time updates (WebSocket)**
   - Broadcast key operations (inspection submitted, job status changes).
5) **Photo storage improvement**
   - Migrate from base64-in-Mongo to object storage.

---

## 4) Success Criteria

### Achieved ✅
- PO accessories visible across ERP and Vendor Portal shipment workflows.
- Backend APIs provide PO-linked accessories payloads.
- RBAC custom roles work end-to-end (backend + UI).
- Vendor can inspect materials + accessories.
- Missing accessories auto-create `material_requests` with consistent schema.
- Vendor can export inspection PDF (includes accessories).
- Product photo upload works; `photo_url` is consistently present for new products.
- Dashboard analytics supports date range filtering.
- Serial tracking supports expandable serial list and full trace timeline.
- Buyer shipment supports per-dispatch PDF export.
- Frontend builds successfully.
- `DESIGN_TECHNICAL_DOCUMENT.md` exists and matches latest behavior.

### Optional follow-ups
- Vendor portal includes full serial list module.
- Product thumbnails fully consistent across all downstream modules.
- Token/session UX improved for long sessions.
- Endpoint pagination and modular routes for maintainability.
