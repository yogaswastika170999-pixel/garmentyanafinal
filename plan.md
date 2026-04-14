# plan.md — Accessories Flow Fix ✅ + RBAC Fix ✅ + Inspection+Accessories ✅ + PDFs ✅ + Product Photos ✅ + Analytics ✅ + Serial Tracking ✅ + Stabilization/Docs 🟡

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
- Upgrade **Dashboard UI/UX + Analytics**:
  - KPI redesign + drilldowns.
  - Date range filtering via `GET /api/dashboard/analytics?from&to`.
- Upgrade **Serial Tracking**:
  - Add `GET /api/serial-list` endpoint.
  - ERP UI: list + expand + trace timeline.
- **Hotfix (critical): Frontend compile error**
  - Fixed JSX fragment mismatch in `ProductionPOModule.jsx` (missing `<>...</>` around action buttons).
  - Verified `yarn build` succeeds (warnings only).

### Current (Now)
- System feature scope is largely complete, but **final batch requires verification**:
  - Comprehensive end-to-end testing for latest UI & backend changes (RBAC buttons, per-dispatch PDFs, thumbnails, auto-material request creation).
  - Create/update **technical documentation** per user request (`DESIGN_TECHNICAL_DOCUMENT.md`).

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

### Phase 3 — Critical Bug Fix: RBAC / Custom Role Enforcement ✅ COMPLETE (Backend) + 🟡 VERIFY (Frontend)
**Goal:** Ensure users with custom roles can do exactly what permissions allow.

#### 3.1 Diagnose current RBAC model ✅
- Root cause: legacy `check_role` only compared role names and ignored custom role permission mappings.

#### 3.2 Implement consistent permission checking ✅
- Backend RBAC:
  - `require_auth` became async and preloads permissions into `user['_permissions']`.
  - `check_role` updated to allow custom roles based on loaded permission keys.
  - Updated route modules to `await require_auth`.
- Frontend:
  - Replace `isSuperAdmin` checks with `hasPerm(userPermissions, 'permission.key')` to show create buttons.

#### 3.3 Add RBAC regression tests ✅
- Added `tests/poc_rbac_custom_role.py`:
  - Create role with all permissions.
  - Create user assigned to that role.
  - Assert user can create PO and create shipment.

#### 3.4 Pending verification (UI) 🟡
- Log in with a **custom role** user and confirm:
  - “Buat PO” visible when `production_po.create` (or equivalent) exists.
  - “Buat Shipment” visible when `vendor_shipment.create` exists.

---

### Phase 4 — Material + Accessories Inspection & Requests ✅ COMPLETE (Inspection) + 🟡 VERIFY (Auto-requests)
**Goal:** When vendor inspects incoming shipment, they can also inspect accessories, and system can auto-create requests for missing accessories (latest batch).

#### 4.1 Data model additions/updates ✅
- Added accessories as a second line group:
  - `vendor_material_inspection_items.item_type` = `material` | `accessory`
  - Inspection header includes: `total_acc_received`, `total_acc_missing`

#### 4.2 API changes ✅
- `POST /api/vendor-material-inspections` supports:
  - `items[]` (materials)
  - `accessory_items[]` (accessories)
- `GET /api/vendor-material-inspections` returns:
  - `items[]` + `accessory_items[]`
- Hardening fix:
  - Inspection POST can infer `vendor_id` from shipment if not provided.

#### 4.3 Auto-create material requests for missing accessories 🟡 TESTING PENDING
- Backend logic injected in `POST /api/vendor-material-inspections` to create records in `material_requests` for missing accessory quantities.
- Verification to perform:
  - Create inspection with missing accessories.
  - Confirm `material_requests` entries are created and linked (shipment/po/vendor).

#### 4.4 UI changes ✅
- Vendor portal inspection form includes accessories inspection table.
- Inspection detail modal includes accessories result.

---

### Phase 5 — Vendor Inspection PDF Export (Materials + Accessories) ✅ COMPLETE
**Goal:** Vendor can export PDF of inspection containing detailed PO & item info.

- Backend: `GET /api/export-pdf?type=vendor-inspection&id={inspection_id}`.
- Frontend: Vendor portal inspection detail includes authenticated **PDF Export** button.

---

### Phase 6 — Product Photos (Master Data + Propagation) ✅ COMPLETE (Master Data) + 🟡 VERIFY (Thumbnails downstream)
**Goal:** Upload and display product photos across system.

#### 6.1 Backend ✅
- `POST /api/products/{id}/photo` uploads and stores a `photo_url`.

#### 6.2 Frontend ✅
- Products module: photo column + upload + preview.

#### 6.3 Pending verification: thumbnails in PO/shipment enrichment 🟡
- Latest batch: backend enrichment adds photo thumbnails to PO/shipment items.
- Verify UI:
  - PO list/detail (ERP) shows thumbnail where intended.
  - Shipment modules show thumbnails where intended.

---

### Phase 7 — Dashboard UI/UX + Analytics Expansion ✅ COMPLETE
**Goal:** More modern and informative analytics with date range filters.

- Endpoint: `GET /api/dashboard/analytics?from=YYYY-MM-DD&to=YYYY-MM-DD`.
- UI: KPI grid, alert bar, drilldowns, charts.

---

### Phase 8 — Serial Tracking Improvements (ERP + Vendor Portal readiness) ✅ COMPLETE (ERP)
**Goal:** Expandable serial list with “ongoing serials” view.

- Backend: `GET /api/serial-list` with filters.
- ERP UI: list + expandable mini timeline + trace timeline.

---

### Phase 9 — Regression Testing + Hardening 🟡 IN PROGRESS
**Goal:** Ensure latest batch is fully verified end-to-end after recent changes.

#### 9.1 Status
- Previous iterations tested:
  - Iteration 1: accessories flow ✅
  - Iteration 2: new features mostly ✅ (backend 93.3% → later fixed vendor_id inference)
- **New finding:** Frontend compile error discovered and fixed ✅

#### 9.2 Testing scope (must run now)
1) **RBAC UI verification** (custom role): create buttons visible.
2) **Buyer Shipment per-dispatch PDF**: buttons render and download correct PDF per dispatch.
3) **Vendor inspection auto-material requests**: missing accessories create `material_requests`.
4) **Product thumbnail enrichment**: appears where expected.

#### 9.3 Tools
- Run `testing_agent_v3` for both backend+frontend flows.
- Add/extend POC scripts if new regression is found.

---

### Phase 10 — Documentation 🟡 NOT STARTED
**Goal:** Fulfill user request to update technical documentation.

#### 10.1 Current state
- `DESIGN_TECHNICAL_DOCUMENT.md` is **missing** in `/app/` (path not found).

#### 10.2 Deliverables
- Create `/app/DESIGN_TECHNICAL_DOCUMENT.md` covering:
  - Architecture overview (3 portals, RBAC, JWT)
  - Key collections and data relationships (PO ↔ accessories ↔ shipment ↔ inspection)
  - New endpoints:
    - `/api/dashboard/analytics`
    - `/api/serial-list`
    - `/api/products/{id}/photo`
    - per-dispatch PDF exports
    - updated `/api/vendor-material-inspections` (accessories + auto-requests)
  - Storage note: `EMERGENT_LLM_KEY` optional; when unset photo storage may be limited/disabled.
  - Testing notes and how to run POC scripts.

---

## 3) Next Actions

1) **Run comprehensive testing (P0)**
   - Execute `testing_agent_v3` for latest batch.
   - Fix any blockers found.

2) **Verify RBAC UI for custom roles (P0)**
   - Confirm “Buat PO” + “Buat Shipment” respect `hasPerm`.

3) **Verify auto-material request creation for missing accessories (P0)**
   - Confirm `material_requests` insertion and linkage.

4) **Create/update `DESIGN_TECHNICAL_DOCUMENT.md` (P0)**

5) **Optional hardening (P1)**
   - Session stability improvements (token TTL / refresh / keep-alive) if timeouts persist.

---

## 4) Success Criteria

### Achieved ✅
- PO accessories visible across ERP and Vendor Portal shipment workflows.
- Backend APIs provide PO-linked accessories payloads.
- RBAC custom roles work at API level; permissions load reliably.
- Vendor can inspect materials + accessories.
- Vendor can export inspection PDF containing PO + invoice + item/accessory inspection data.
- Product photo upload works in master data.
- Dashboard analytics supports date range filtering.
- Serial tracking supports expandable serial list and full trace timeline.
- Frontend builds successfully after fixing `ProductionPOModule.jsx` syntax error.

### Pending verification 🟡
- Custom role **UI**: create buttons visible and functional.
- Buyer Shipment **per-dispatch** PDF export works end-to-end.
- Auto-create `material_requests` for missing accessories works and persists in DB.
- Photo thumbnails/enrichment appear in intended PO/shipment screens.
- `DESIGN_TECHNICAL_DOCUMENT.md` exists and matches latest behavior.

### Follow-up success criteria (optional enhancements)
- Vendor portal includes full serial list module.
- Missing accessories automatically trigger additional shipment request workflow (if desired beyond material_requests).
- Product thumbnails consistent across all downstream modules.
- Token/session UX improved for long sessions.
