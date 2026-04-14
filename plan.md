# plan.md — Accessories Flow Fix ✅ + RBAC Fix + Inspection+Accessories + PDFs + Product Photos + Analytics + Serial Tracking

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
- Add regression guard:
  - `tests/poc_po_accessories_flow.py` passing (**23/23**)
  - Testing agent verified **100%** for accessories visibility.

### Current (Next)
- Fix **RBAC / Custom Role** permission enforcement so feature access matches Role Management settings.
- Extend **Material Inspection** to include **Accessories Inspection**:
  - Vendor inspects both materials and accessories.
  - Missing accessories can generate **additional shipment requests** including accessories.
- Add **Vendor Inspection PDF export** with comprehensive context:
  - PO info (No PO), Invoice No, product metadata, qty sent/received/missing.
  - Include **accessories inspection lines**.
- Add **Product Photos**:
  - Upload photo in Product master.
  - Ensure downstream screens show the photo.
- Upgrade **Dashboard UI/UX + Analytics**:
  - More visualizations, modern layout, and **date range filters**.
- Upgrade **Serial Tracking** (ERP + Vendor Portal):
  - Expandable **Serial Number list** and “ongoing” serials with key info.

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
   - Testing agent: **100% success**.

**Phase 2 user stories (met)**
1. Admin sees accessories in PO detail.
2. Admin sees PO accessories when preparing shipment.
3. Vendor sees PO accessories in portal.

---

### Phase 3 — Critical Bug Fix: RBAC / Custom Role Enforcement (Next)
**Goal:** Ensure users with custom roles can do exactly what permissions allow.

#### 3.1 Diagnose current RBAC model
- Identify current permission data model:
  - Role documents (permissions structure, module keys, action keys).
  - How user documents reference roles.
- Trace permission checks across endpoints:
  - Especially `POST /api/production-pos` and `POST /api/vendor-shipments`.

#### 3.2 Implement consistent permission checking
- Create/standardize helper:
  - `has_permission(user, module, action)` (e.g., `production_po:create`, `vendor_shipment:create`).
- Ensure role evaluation works for:
  - `superadmin` hard allow
  - `admin` default allow
  - custom roles: allow/deny based on permissions
- Align frontend route/module guards to the same permission keys.

#### 3.3 Add RBAC regression tests
- Add `tests/poc_rbac_custom_role.py`:
  - Create role with “all access”.
  - Create user assigned to that role.
  - Assert user can create PO and create shipment.

**Phase 3 user stories**
1. As admin, I can create a custom role with full access and the user can create PO/shipment.
2. As admin, I can restrict a module and the user is blocked consistently (UI + API).

---

### Phase 4 — Material + Accessories Inspection & Requests (Core Workflow)
**Goal:** When vendor inspects incoming shipment, they can also inspect accessories, and request additional shipment for missing accessories.

#### 4.1 Data model additions/updates
- Decide whether to:
  - Extend existing `inspections` to include accessory lines, **or**
  - Create `accessory_inspection_items` linked to the material inspection.
- Track accessory inspection per shipment:
  - `qty_sent`, `qty_received`, `qty_missing` for each accessory.

#### 4.2 API changes
- Add/extend endpoints so vendor can submit accessory inspection with material inspection.
- Enable requests to include accessory lines:
  - Additional requests can include both material items + accessory items.
- Ensure approval flow can generate:
  - material child shipment items (existing)
  - accessory child shipment items (new, likely via `accessory_shipments`)

#### 4.3 UI changes
- Vendor portal:
  - Inspection screen includes accessories table (parallel to material table).
  - Missing accessories can be selected to request additional shipment.
- ERP:
  - Inspection detail includes accessories result.
  - Requests view shows accessory lines and quantities.

**Phase 4 user stories**
1. As vendor, I can inspect accessories for a shipment.
2. As vendor, if accessories are missing, I can request additional shipment including accessories.
3. As admin, I can approve and generate follow-up shipments/records.

---

### Phase 5 — Vendor Inspection PDF Export (Materials + Accessories)
**Goal:** Vendor can export PDF of inspection containing detailed PO & item info.

#### 5.1 PDF content requirements
Include for **materials**:
- No PO
- No Invoice
- Product name
- Product category
- Size, color, SKU
- Qty shipped
- Qty received
- Qty missing

Include for **accessories**:
- Accessory name/code/category
- Qty shipped/received/missing

#### 5.2 Implementation
- Backend:
  - New endpoint: `GET /api/export-pdf?type=vendor-inspection&id={inspection_id}`
  - Query joins:
    - inspection → shipment → PO → invoice (if linked)
    - shipment_items + inspection_items
    - accessory_shipment_items + accessory_inspection_items
- Frontend:
  - Vendor portal: button “Export PDF Inspeksi” on inspection detail.

#### 5.3 Tests
- Generate PDF and verify:
  - Response is PDF
  - Contains PO number and expected headers

---

### Phase 6 — Product Photos (Master Data + Propagation)
**Goal:** Upload and display product photos across system.

#### 6.1 Backend
- Add field(s) on `products`:
  - `photo_url` (single) or `photos[]`
- Add upload endpoint:
  - `POST /api/products/{id}/photo` (store in existing storage mechanism)

#### 6.2 Frontend
- Products module:
  - Upload control + preview.
- Downstream propagation:
  - PO item lines show product thumbnail.
  - Shipment items show product thumbnail.
  - Anywhere product is referenced: optional image fallback.

#### 6.3 Tests
- Upload photo and verify returned URL persists and renders.

---

### Phase 7 — Dashboard UI/UX + Analytics Expansion
**Goal:** More modern and informative analytics with date range filters.

#### 7.1 Date filter
- Week / Month / Custom date range.
- Applies to KPI + charts.

#### 7.2 Add visualizations (proposal)
- On-time delivery rate (PO vs delivery deadline)
- Vendor lead time distribution (shipment sent → received → inspected)
- Missing/defect rate trends (by vendor, by product)
- Work-in-progress (WIP) aging buckets
- Production throughput (daily/weekly output)

#### 7.3 UI refresh
- Modern card layout, drilldowns, consistent color system.

---

### Phase 8 — Serial Tracking Improvements (ERP + Vendor Portal)
**Goal:** Add expandable list of serial numbers and “ongoing serials” view.

#### 8.1 ERP Serial Tracking
- Add a table of serial numbers with:
  - PO number, product, vendor
  - ordered, shipped, received, remaining
  - current status + last event timestamp
- Expand row to show timeline/events.

#### 8.2 Vendor Portal Serial Tracking
- Similar list, filtered to vendor’s POs/shipments.
- Expand row to show active/in-progress serials and key shipment links.

---

### Phase 9 — Regression Testing + Hardening
- Keep `tests/poc_po_accessories_flow.py` as regression gate.
- Add tests for:
  - RBAC custom roles
  - inspection+accessories workflow
  - vendor inspection PDF export
  - product photo upload
- Run end-to-end regression after each phase.

---

## 3) Next Actions
1) **RBAC fix first**: reproduce the role/user issue and patch permission checks.
2) Implement accessories in inspection + additional requests for accessories.
3) Add vendor inspection PDF export.
4) Add product photo upload and propagate thumbnails.
5) Start dashboard analytics expansion + date filters.
6) Implement serial tracking expandable list for ERP + vendor portal.

---

## 4) Success Criteria
### Already achieved
- PO accessories are visible across ERP and Vendor Portal shipment workflows.
- Backend APIs provide PO-linked accessories payloads.
- POC script passes (**23/23**) and testing agent success (**100%**).

### New success criteria
- **RBAC**: Custom roles work reliably; permissions match UI + API behavior.
- **Inspection**: Vendor can inspect materials + accessories; missing accessories can trigger additional requests.
- **PDF**: Vendor can export inspection PDF containing PO + invoice + item/accessory inspection data.
- **Product photos**: Upload + display across all relevant modules.
- **Dashboard**: Modern analytics with date range filters and multiple meaningful visualizations.
- **Serial tracking**: Expandable serial list with ongoing serials and key metrics in ERP and vendor portal.
