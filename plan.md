# plan.md — Accessories Flow ✅ + RBAC ✅ + Inspection+Accessories ✅ + PDFs ✅ + Product Photos ✅ + Analytics ✅ + Serial Tracking ✅ + Stabilization/Docs ✅ + **Invoice Edit Approval System ✅ COMPLETE**

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
  - Verified frontend builds successfully.
- **Documentation delivered**
  - Created `/app/DESIGN_TECHNICAL_DOCUMENT.md` with complete architecture + DB + API + feature documentation.

- ✅ **Invoice Edit Approval System (P0)** untuk menjaga integritas data finansial:
  - Hanya **Admin ERP (superadmin/admin)** yang bisa mengajukan request edit
  - Hanya **Superadmin/Admin** yang bisa approve/reject
  - Jika approved: **invoice auto-update** + **histori perubahan tersimpan** + **UI histori**
  - **Real-time** notifikasi pending request (MVP: polling badge count di Sidebar setiap 30 detik)
  - Backend indexes untuk performa (`invoice_edit_requests`, `invoice_change_history`)
  - End-to-end testing sukses (**overall 96.9%**, frontend **100%**, backend **93.8%**) — 1 minor test-design issue (bukan bug)

### Current (Now)
- Tidak ada P0 terbuka.
- Monitoring: verifikasi usage harian (apakah approval flow dipakai intens) + pantau log untuk edge cases.

### Next (After P0)
- Resolve **Production Monitoring job-level `shipped_qty` display** (P2, currently blocked) dengan refactor endpoint/UI.
- Optional/future: session longevity, modularization `server.py`, pagination, real-time WebSocket (true realtime, bukan polling).

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

---

### Phase 8 — Serial Tracking Improvements (ERP + Vendor Portal readiness) ✅ COMPLETE
**Goal:** Expandable serial list with “ongoing serials” view.

- Backend: `GET /api/serial-list` with filters.
- ERP UI: list + expandable mini timeline + trace timeline.

---

### Phase 9 — Regression Testing + Hardening ✅ COMPLETE
**Goal:** Ensure latest batch is fully verified end-to-end after recent changes.

#### 9.1 Test iterations ✅
- Iteration 1: accessories flow ✅
- Iteration 2: new features mostly ✅
- Iteration 3: comprehensive ✅
  - Found 2 medium issues (photo_url init, material request schema mismatch) → fixed ✅

#### 9.2 Evidence ✅
- Test reports:
  - `/app/test_reports/iteration_1.json`
  - `/app/test_reports/iteration_2.json`
  - `/app/test_reports/iteration_3.json`

---

### Phase 10 — Documentation ✅ COMPLETE
**Goal:** Fulfill user request to update technical documentation.

- Created `/app/DESIGN_TECHNICAL_DOCUMENT.md`.

---

### Phase 11 — Invoice Edit Approval System (P0) ✅ COMPLETE
**Goal:** Approval flow formal untuk perubahan invoice agar ada kontrol, audit trail, dan notifikasi real-time.

#### 11.1 Scope & Rules ✅
- **Requester:** hanya **Admin ERP**.
- **Approver:** hanya **Superadmin/Admin**.
- **Fields:** semua field invoice termasuk `invoice_items`, `discount`, `notes`, `total_amount`, dll.
- **Approval action:** jika Approved → **invoice auto-update**.
- **Audit:** simpan histori perubahan lengkap + tautkan ke approval request.
- **Real-time (MVP):** polling badge count pending request di Sidebar (30 detik).

#### 11.2 Backend (FastAPI + MongoDB) ✅
1) **Collections + indexes**
   - `invoice_edit_requests`
   - `invoice_change_history`
   - Indexes:
     - `invoice_edit_requests`: `invoice_id`, `status`, `requested_at`
     - `invoice_change_history`: `invoice_id`, `changed_at`

2) **API Endpoints (implemented)**
   - `POST /api/invoice-edit-requests`
   - `GET /api/invoice-edit-requests?status=&q=&from=&to=`
   - `GET /api/invoice-edit-requests/{id}`
   - `PUT /api/invoice-edit-requests/{id}/approve` (auto-update invoice + insert history)
   - `PUT /api/invoice-edit-requests/{id}/reject`
   - `GET /api/invoices/{invoice_id}/change-history`

3) **Validasi utama**
   - Tidak bisa request edit jika sudah ada request `Pending` untuk invoice yang sama.
   - Tidak bisa request edit untuk invoice `Superseded`.
   - Tidak bisa approve/reject request yang status-nya bukan `Pending`.

#### 11.3 Frontend (React) ✅
1) **Module baru:** `ApprovalModule.jsx`
   - List/filter requests (Pending/Approved/Rejected)
   - Detail modal per request dengan perbandingan **Before vs After**
   - Approve/Reject + notes

2) **Update existing invoice UI:** `ManualInvoiceModule.jsx`
   - Tombol **Request Edit**
   - Tombol **Histori Perubahan** (fetch `change-history`)

3) **Sidebar badge + polling realtime (MVP)**
   - Menu baru: `invoice-approval`
   - Badge pending count (fetch `GET /api/invoice-edit-requests?status=Pending`) setiap 30 detik

#### 11.4 Testing ✅
- Test report: `/app/test_reports/iteration_4.json`
  - **Overall:** 96.9% (31/32)
  - **Frontend:** 100% (UI + integrasi OK)
  - **Backend:** 93.8% (1 minor test-design issue: mencoba approve request yang sudah approved)
- Test script tambahan: `/app/invoice_edit_approval_test.py`

---

## 3) Next Actions

### P0 (Closed)
- ✅ Invoice Edit Approval System sudah live dan sudah ditest.

### P1 (Optional / Future)
1) **Production Monitoring job-level `shipped_qty` display** (P2 tapi recurring)
   - Refactor backend `/api/production-monitoring-v2` atau tambah endpoint detail job.
   - Update `ProductionMonitoringModule.jsx` mapping.
2) **Session stability improvements**
   - Consider refresh token / keep-alive / longer TTL.
3) **Backend modularization**
   - Split monolithic `/app/backend/server.py` into domain routers under `/app/backend/routes/`.
4) **Server-side pagination**
   - For large lists (PO, shipments, jobs, logs).
5) **Real-time updates (WebSocket)**
   - Upgrade polling → WebSocket broadcasting untuk approval dan event penting lainnya.
6) **Photo storage improvement**
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

### New (Phase 11) Achieved ✅
- Admin dapat membuat **request edit invoice** tanpa mengubah invoice langsung.
- Superadmin/Admin dapat **approve/reject** request dari dashboard.
- Saat approved, invoice **auto-update** dan sistem menyimpan **invoice_change_history**.
- UI menyediakan **Histori Perubahan** invoice.
- Sidebar menampilkan **badge pending** dan update secara near real-time via polling.
- Semua aksi terekam di `activity_logs`.

### Optional follow-ups
- Upgrade polling → WebSocket realtime untuk approval notifications.
- Tambah endpoint count khusus (mis. `GET /api/invoice-edit-requests/count?status=Pending`) agar polling lebih ringan.
- Tambah navigasi “Quick link ke invoice detail” yang benar-benar melakukan navigate (saat ini masih placeholder alert di `ApprovalModule.jsx`).
