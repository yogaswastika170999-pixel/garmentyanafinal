# Garment ERP System — Design & Technical Document

**Version:** 8.0  
**Last Updated:** 12 April 2026  
**Status:** Active Development  
**Platform:** React (CRA) + FastAPI + MongoDB  
**Repository:** /app  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Database Schema](#4-database-schema)
5. [API Endpoints](#5-api-endpoints)
6. [Frontend Modules](#6-frontend-modules)
7. [Three Portal System](#7-three-portal-system)
8. [RBAC — Role-Based Access Control](#8-rbac--role-based-access-control)
9. [Core Business Logic](#9-core-business-logic)
10. [Implemented Features](#10-implemented-features)
11. [Import / Export / Reports](#11-import--export--reports)
12. [PDF Export System](#12-pdf-export-system)
13. [Reminder & Action System](#13-reminder--action-system)
14. [Dashboard & Analytics](#14-dashboard--analytics)
15. [Infrastructure & DevOps](#15-infrastructure--devops)
16. [Security Considerations](#16-security-considerations)
17. [Development History](#17-development-history)
18. [Known Issues & Remaining Items](#18-known-issues--remaining-items)
19. [Future Implementation Recommendations](#19-future-implementation-recommendations)
20. [Appendix](#20-appendix)

---

## 1. Executive Summary

### 1.1 About the System

Garment ERP is an Enterprise Resource Planning system for the garment industry. It manages the full production lifecycle from Purchase Order (PO) through to buyer delivery. The system has three separate portals:

- **ERP Admin Portal** — Full management of POs, shipments, production, finance, reminders, and reporting
- **Vendor Portal** — Vendors receive material, inspect, produce, report progress, and respond to reminders
- **Buyer Portal** — Buyers view their POs, track shipments, and download dispatch PDFs

### 1.2 Functional Scope

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GARMENT ERP SYSTEM v8.0                             │
├───────────────────┬────────────────────────────┬────────────────────────────┤
│ MASTER DATA       │ OPERATIONS                 │ FINANCE & REPORTING        │
├───────────────────┼────────────────────────────┼────────────────────────────┤
│ • Products        │ • Production PO            │ • Manual Invoice (AP/AR)   │
│ • Variants        │ • Vendor Shipment          │ • Payments                 │
│ • Vendors         │ • Material Inspection      │ • Hutang Vendor (AP)       │
│ • Buyers          │ • Production Jobs          │ • Piutang Buyer (AR)       │
│ • Accessories     │ • Progress Tracking        │ • Rekap Keuangan           │
│ • Users & Roles   │ • Buyer Shipment           │ • Reports (9 types)        │
│ • Company Info    │ • Retur Produksi           │ • PDF Export (16 types)    │
│                   │ • Material Request         │ • Excel Export (6 types)   │
│                   │ • Defect Report            │ • Import (4 types)         │
│                   │ • Accessory Workflow        │ • PDF Config Presets       │
│                   │ • Serial Tracking          │                            │
│                   │ • Distribusi Kerja         │                            │
│                   │ • Monitoring               │                            │
├───────────────────┼────────────────────────────┼────────────────────────────┤
│ COMMUNICATION     │ ANALYTICS                  │ SYSTEM                     │
├───────────────────┼────────────────────────────┼────────────────────────────┤
│ • Reminder System │ • Interactive Dashboard    │ • JWT Auth + RBAC          │
│ • Vendor Inbox    │ • KPI Drilldowns           │ • Activity Logging         │
│ • Response Track  │ • On-Time Rate             │ • Global Search            │
│                   │ • Status Breakdown Charts  │ • Cascade Delete           │
│                   │ • Vendor Production Rank   │ • Rate Limiting            │
└───────────────────┴────────────────────────────┴────────────────────────────┘
```

### 1.3 System Statistics

| Component | Count |
|-----------|-------|
| Backend Python files | 9 files, ~5,144 lines |
| Frontend JSX components | 38 files |
| API Endpoints | 145 (135 core + 10 modular) |
| Database Collections | 40 |
| Frontend App.js | ~288 lines |
| PDF Export Types | 16 |

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       KUBERNETES CLUSTER                         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────┐       │
│  │   INGRESS    │──▶│   REACT (CRA)    │  │   MONGODB    │       │
│  │   (NGINX)    │  │   (Port 3000)    │  │   (Local)    │       │
│  │              │  │  38 components   │  │  40 colls    │       │
│  │  /api/* ─────┤──▶│                  │  │              │       │
│  │  /ws/* ──────┤──▶│   FASTAPI        │──▶│              │       │
│  │  /* ─────────┤──▶│   (Port 8001)    │  │              │       │
│  └──────────────┘  │  145 endpoints   │  └──────────────┘       │
│                    └──────────────────┘                          │
│                          │                                       │
│                    ┌─────▼────────────┐                          │
│                    │ EMERGENT OBJECT  │                          │
│                    │ STORAGE (S3)     │                          │
│                    └──────────────────┘                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  SUPERVISOR: react (port 3000) + fastapi (port 8001)    │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Business Process Flow

```
PO Created ──▶ Vendor Shipment ──▶ Material Inspection ──▶ Production Job
   │                 │                     │                      │
   [Buyer]      [Accessories]         [Missing?]          [Progress Report]
   [linked]     [shipped too]              │                      │
                                    Material Request       Monitoring
                                           │                      │
                                    Additional Shipment     Job Complete
                                    (with PO context)            │
                                           │              Buyer Shipment
                                    Vendor Receive &     (dispatch 1, 2, 3...)
                                    Inspect (child)            │
                                           │              Invoice Created
                                    Recalculate Jobs           │
                                    (aggregate all)        Payment
                                           │
                                    Available Qty Updated
```

### 2.3 Backend File Structure

```
/app/backend/
├── server.py              # Main app + core routes (~4,540 lines)
├── database.py            # MongoDB connection (motor async)
├── auth.py                # JWT auth, bcrypt, token creation, seeding
├── cascade_delete.py      # Cascade delete for PO and Vendor
├── storage.py             # Emergent Object Storage integration
├── routes/
│   ├── __init__.py
│   ├── buyer_portal.py    # Buyer portal endpoints (6 routes)
│   ├── file_storage.py    # File upload/download (3 routes)
│   └── websocket.py       # WebSocket real-time (1 route)
├── requirements.txt
└── .env
```

### 2.4 Frontend File Structure

```
/app/frontend/src/
├── App.js                 # Main SPA router (~288 lines)
├── App.css                # Global styles + Tailwind + responsive
├── components/
│   ├── erp/
│   │   ├── Login.jsx
│   │   ├── Sidebar.jsx
│   │   ├── Dashboard.jsx               # Interactive dashboard (KPI drilldowns, charts, reminders)
│   │   ├── ProductsModule.jsx
│   │   ├── GarmentsModule.jsx
│   │   ├── BuyersModule.jsx
│   │   ├── AccessoryModule.jsx
│   │   ├── ProductionPOModule.jsx
│   │   ├── VendorShipmentModule.jsx
│   │   ├── BuyerShipmentModule.jsx
│   │   ├── ProductionReturnModule.jsx
│   │   ├── WorkOrderModule.jsx
│   │   ├── ProductionMonitoringModule.jsx
│   │   ├── ProductionProgressModule.jsx
│   │   ├── SerialTrackingModule.jsx
│   │   ├── AccountsPayableModule.jsx
│   │   ├── AccountsReceivableModule.jsx
│   │   ├── ManualInvoiceModule.jsx
│   │   ├── InvoiceModule.jsx
│   │   ├── PaymentModule.jsx
│   │   ├── FinancialRecapModule.jsx
│   │   ├── ReportsModule.jsx
│   │   ├── CompanySettingsModule.jsx
│   │   ├── UserManagementModule.jsx
│   │   ├── RoleManagementModule.jsx
│   │   ├── PDFConfigModule.jsx          # PDF Export Configuration (NEW v8)
│   │   ├── ActivityLogModule.jsx
│   │   ├── HelpGuideModule.jsx
│   │   ├── VendorPortalApp.jsx          # Vendor portal + Reminder Inbox (UPDATED v8)
│   │   ├── BuyerPortalApp.jsx
│   │   ├── DataTable.jsx
│   │   ├── Modal.jsx
│   │   ├── SearchableSelect.jsx
│   │   ├── ImportExportPanel.jsx
│   │   ├── FileAttachmentPanel.jsx
│   │   ├── POWorkflowIndicator.jsx
│   │   ├── StatusBadge.jsx
│   │   └── ConfirmDialog.jsx
│   └── ui/                              # Shadcn/ui components (40+ files)
├── hooks/
├── lib/
└── index.js
```

---

## 3. Technology Stack

### 3.1 Core Technologies

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Frontend | React (CRA + Craco) | 19.x | Single-page application |
| Backend | FastAPI (Python) | Latest | Async, high-performance |
| Database | MongoDB | Latest | Motor async driver |
| CSS | Tailwind CSS | 3.x | Utility-first, responsive |
| UI Components | Shadcn/ui + Custom | Latest | 40+ base + 38 custom |
| Icons | Lucide React | Latest | Icon library |
| Charts | Recharts | Latest | AreaChart, PieChart, BarChart |
| File Storage | Emergent Object Storage | — | Persistent S3-compatible |
| Real-time | WebSocket (FastAPI) | — | Channel-based broadcast |
| PDF Generation | ReportLab | 4.4.x | 16 PDF export types |
| Excel | OpenPyXL | 3.1.x | Import/Export |

### 3.2 Backend Libraries

| Library | Purpose |
|---------|---------|
| `motor` | Async MongoDB driver |
| `pyjwt` + `bcrypt` | JWT authentication + password hashing |
| `openpyxl` | Excel import/export |
| `reportlab` | PDF generation (16 types) |
| `python-multipart` | File uploads |
| `requests` | Object storage API |
| `recharts` (frontend) | Interactive data visualization |

---

## 4. Database Schema

### 4.1 Collections Overview (40 Collections)

```
┌──────────────────────────────────────────────────────────────────┐
│                    DATABASE COLLECTIONS (40)                      │
├──────────────────────┬───────────────────────────────────────────┤
│ MASTER DATA          │ users, products, product_variants,        │
│                      │ garments, buyers, accessories,            │
│                      │ company_settings, roles,                  │
│                      │ role_permissions, permissions             │
├──────────────────────┼───────────────────────────────────────────┤
│ PURCHASE ORDER       │ production_pos, po_items, po_accessories  │
├──────────────────────┼───────────────────────────────────────────┤
│ VENDOR OPERATIONS    │ vendor_shipments, vendor_shipment_items,  │
│                      │ vendor_material_inspections,              │
│                      │ vendor_material_inspection_items          │
├──────────────────────┼───────────────────────────────────────────┤
│ PRODUCTION           │ production_jobs, production_job_items,    │
│                      │ production_progress, work_orders          │
├──────────────────────┼───────────────────────────────────────────┤
│ BUYER OPERATIONS     │ buyer_shipments, buyer_shipment_items     │
├──────────────────────┼───────────────────────────────────────────┤
│ QUALITY CONTROL      │ material_requests, material_defect_reports│
│                      │ production_returns, production_return_items│
├──────────────────────┼───────────────────────────────────────────┤
│ ACCESSORIES          │ accessory_shipments,                      │
│                      │ accessory_shipment_items,                 │
│                      │ accessory_inspections,                    │
│                      │ accessory_inspection_items,               │
│                      │ accessory_defects, accessory_requests     │
├──────────────────────┼───────────────────────────────────────────┤
│ FINANCE              │ invoices, invoice_adjustments, payments   │
├──────────────────────┼───────────────────────────────────────────┤
│ COMMUNICATION        │ reminders (NEW v8)                        │
├──────────────────────┼───────────────────────────────────────────┤
│ CONFIGURATION        │ pdf_export_configs (NEW v7)               │
├──────────────────────┼───────────────────────────────────────────┤
│ SYSTEM               │ activity_logs, attachments                │
└──────────────────────┴───────────────────────────────────────────┘
```

### 4.2 New Schema Definitions (v7–v8)

#### `pdf_export_configs` (NEW v7)
```javascript
{ id: UUID, pdf_type: String, name: String, columns: [String],
  is_default: Boolean, created_by: String, created_at, updated_at }
```

#### `reminders` (NEW v8)
```javascript
{ id: UUID, vendor_id: UUID, vendor_name: String,
  po_id: String, po_number: String,
  reminder_type: "general|production|shipment|quality",
  subject: String, message: String, priority: "normal|high|urgent",
  status: "pending|responded|closed",
  response: String, response_date: DateTime, responded_by: String,
  created_by: String, created_at, updated_at }
```

### 4.3 Data Integrity Rules

- **UUID as Primary Key**: All records use UUID v4, not MongoDB ObjectID
- **Internal UUID Matching**: System uses `po_item_id`, `vendor_shipment_item_id`, `job_item_id` (UUIDs) for joins — NEVER matches by visible fields
- **Duplicate-Safe**: PO number, SKU, serial number, size, color may all be duplicated — records stay separate via UUID lineage
- **Cascade Delete**: Deleting a PO cascades to all shipments, inspections, jobs, progress, buyer shipments, invoices, payments, returns, and attachments
- **Orphan Repair**: `recalculate-jobs` auto-backfills `po_item_id` on child shipment items that are missing it (NEW v8)

---

## 5. API Endpoints (145 Total)

### 5.1–5.8 (Unchanged from v6 — see prior document sections)

### 5.9 PDF Export & Configuration (NEW v7–v8)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/export-pdf?type=...` | PDF export (16 types supported) |
| GET | `/api/pdf-export-columns?type=...` | Available column keys/labels for a PDF type |
| CRUD | `/api/pdf-export-configs[/{id}]` | PDF export preset management |

**Supported PDF Types (16):**
- Documents: `production-po`, `vendor-shipment`, `buyer-shipment`, `buyer-shipment-dispatch`, `production-return`, `material-request`, `production-report`
- Reports: `report-production`, `report-progress`, `report-financial`, `report-shipment`, `report-defect`, `report-return`, `report-missing-material`, `report-replacement`, `report-accessory`

### 5.10 Reminder System (NEW v8)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reminders` | List reminders (vendor-filtered if vendor role) |
| POST | `/api/reminders` | Create reminder to vendor |
| PUT | `/api/reminders/{id}` | Update/respond to reminder |
| DELETE | `/api/reminders/{id}` | Delete reminder |

---

## 6. Frontend Modules (38 Components)

| # | Module | File | Description | Status |
|---|--------|------|-------------|--------|
| 1 | Dashboard | `Dashboard.jsx` | Interactive KPI cards, drilldown modals, charts, reminders | UPDATED v8 |
| 2–24 | (Unchanged from v6) | | |
| 25 | Vendor Portal | `VendorPortalApp.jsx` | Complete vendor-facing app + Reminder Inbox | UPDATED v8 |
| 26 | Buyer Portal | `BuyerPortalApp.jsx` | Read-only buyer portal | |
| 27 | PDF Config | `PDFConfigModule.jsx` | PDF export column presets | NEW v7 |

---

## 7–8. Three Portal System & RBAC
(Unchanged from v6 — see prior document)

---

## 9. Core Business Logic

### 9.1 PO Staged Status Lifecycle (Unchanged)

### 9.2 Quantity Lifecycle (Unchanged)

### 9.3 Material Continuation — UPDATED v8

**Request Numbering** (NEW v8):
- Format: `REQ-ADD-{count_for_this_po}-{po_number}` (e.g., `REQ-ADD-1-PO-001`)
- Previous format: `REQ-ADD-{global_count}` (deprecated)

**Child Shipment Data Propagation** (FIXED v8):
- Child shipment items now inherit `serial_number` from parent shipment items
- Child shipment items inherit `po_item_id` linkage (critical for aggregation)
- Admin notes stored as `notes_for_vendor` and visible in Vendor Portal
- Vendor request `notes` adopted as `reason` (no more hardcoded reasons)

**Continuation Aggregation** (FIXED v8):
- `available_qty` in production job items = sum(received across ALL shipments for that `po_item_id`) — parent + ALL children
- `recalculate-jobs` endpoint now:
  1. Backfills orphan `po_item_id` on child shipment items (matches by sku+size+color)
  2. Aggregates inspection data across all shipments per `po_item_id`
  3. Updates `available_qty` and `total_received_qty`

**Distribusi Kerja Aggregation** (FIXED v8):
- Rewritten to aggregate from PO items (not individual shipment items)
- `total_received` = sum of received qty across ALL inspected shipments per `po_item_id`
- Correctly shows production progress relative to ordered qty

### 9.4 Serial Tracking — UPDATED v8

- **Not Shipped** calculation fixed: `max(0, ordered - shipped)` (was `max(0, produced - shipped)`)
- **Timeline events** now include:
  - `event`: Human-readable event name in Indonesian (e.g., "PO Dibuat", "Inspeksi Material", "Progres Produksi")
  - `details`: Descriptive text with quantities and context

---

## 10. Implemented Features

### Master Data ✅ (Unchanged)

### Production Operations ✅
- [x] All v6 features
- [x] Material request numbering with PO context (v8)
- [x] Child shipment serial number propagation (v8)
- [x] Admin notes visible in vendor portal (v8)
- [x] Continuation aggregation fixed (available_qty, distribusi kerja) (v8)

### Quality Control ✅ (Unchanged)

### Finance ✅ (Unchanged)

### PDF Export ✅ (NEW v7)
- [x] 16 PDF export types fully functional
- [x] PDF Export Configuration module (column presets)
- [x] Company header/footer support
- [x] No-data graceful handling

### Dashboard & Analytics ✅ (NEW v8)
- [x] Interactive KPI cards with click-to-drilldown
- [x] Compact alert pills (replaced large notification panel)
- [x] Status Job Produksi pie chart (with real data)
- [x] Top Vendor by Production bar chart (with real data)
- [x] Production trends area chart (6 months)
- [x] PO status breakdown
- [x] On-Time Rate metric
- [x] Reminder count and status

### Reminder & Action System ✅ (NEW v8)
- [x] ERP: Send reminders to vendors (subject, message, PO reference, priority)
- [x] Vendor Portal: Inbox with pending/responded sections
- [x] Vendor Portal: Inline response form
- [x] ERP: Track response status and history

### System Features ✅
- [x] All v6 features
- [x] Serial tracking with filled timeline events (v8)
- [x] Orphan child shipment item repair (v8)

---

## 11. Import / Export / Reports
(Unchanged from v6 — see prior document)

---

## 12. PDF Export System (NEW v7)

### 12.1 Supported Types (16)

| Type | Category | Document |
|------|----------|----------|
| `production-po` | Document | Surat Perintah Produksi (SPP) |
| `vendor-shipment` | Document | Surat Jalan Material |
| `buyer-shipment` | Document | Buyer Shipment Summary |
| `buyer-shipment-dispatch` | Document | Per-dispatch buyer delivery note |
| `production-return` | Document | Surat Retur Produksi |
| `material-request` | Document | Surat Permohonan Material |
| `production-report` | Report | Full production report |
| `report-production` | Report | Laporan Produksi |
| `report-progress` | Report | Laporan Progres |
| `report-financial` | Report | Laporan Keuangan |
| `report-shipment` | Report | Laporan Pengiriman |
| `report-defect` | Report | Laporan Defect |
| `report-return` | Report | Laporan Retur |
| `report-missing-material` | Report | Laporan Material Hilang |
| `report-replacement` | Report | Laporan Material Pengganti |
| `report-accessory` | Report | Laporan Aksesoris |

### 12.2 PDF Configuration

Admins can create **presets** per PDF type to control which columns appear:
- Required columns (e.g., "No", "Qty") cannot be unchecked
- Multiple presets per type; one can be set as **default**
- Default preset auto-applied during export
- Column definitions returned by `/api/pdf-export-columns?type=...`

---

## 13. Reminder & Action System (NEW v8)

### 13.1 Flow

```
ERP Admin creates reminder ──▶ Saved in `reminders` collection
                                     │
                              Vendor Portal shows in Inbox
                                     │
                              Vendor responds with message
                                     │
                              Status: pending → responded
                                     │
                              ERP Admin sees response in dashboard
```

### 13.2 Reminder Fields

- **Subject**, **Message**, **PO Number** (optional), **Priority** (normal/high/urgent)
- **Response** text from vendor
- **Status tracking**: `pending` → `responded` → `closed`

---

## 14. Dashboard & Analytics (UPDATED v8)

### 14.1 KPI Cards (12)

All cards are **clickable** and open a drilldown modal with detailed summary and navigation links.

| Card | Metric | Drilldown |
|------|--------|-----------|
| Total PO | Count + active | Status breakdown + samples |
| Active Jobs | Running jobs | Job status distribution |
| Progress Produksi | Global % | Progress bar + pending stats |
| On-Time Rate | % delivered on time | Rate explanation |
| Pending Shipment | Awaiting receipt | → Vendor Shipment module |
| Req. Tambahan | Pending requests | → Vendor Shipment module |
| Retur Produksi | Pending returns | → Production Returns module |
| Reminders | Pending + responded | Full reminder list |
| Invoice AR | Buyer invoices | → Accounts Receivable |
| Invoice AP | Vendor invoices | → Accounts Payable |
| Outstanding | Total outstanding | → Invoices module |
| Gross Margin | Revenue − cost | → Financial Recap |

### 14.2 Charts

- **Production Trends** (AreaChart): 6-month PO count + production volume
- **Status Job Produksi** (PieChart): Job status distribution
- **Top Vendor by Production** (Bar ranking): Vendor production output
- **PO Status Breakdown**: Status color badges with counts
- **Reminder Status**: Compact list of recent reminders

### 14.3 Compact Alerts

Replaced large notification panel with **pill badges**:
- Red pill: Overdue POs
- Amber pill: Near-deadline POs
- Orange pill: Unpaid invoices

---

## 15. Infrastructure & DevOps
(Unchanged from v6 — see prior document)

---

## 16. Security Considerations
(Unchanged from v6 — see prior document)

---

## 17. Development History

| Phase | Date | Scope | Backend | Frontend |
|-------|------|-------|---------|----------|
| Phase 1 | Apr 2026 | POC: duplicate-safe lineage | 100% | — |
| Phase 2 | Apr 2026 | Staged PO, quantity lifecycle, serial tracking, accessories, RBAC | 96.3% | 100% |
| Phase 3 | Apr 2026 | Accessory workflows, dispatch PDF, 9 reports, import/export, dashboard | 97.8% | 100% |
| Phase 4 | Apr 2026 | Buyer portal, RBAC UI, persistent storage, modularization | 96.4% | 100% |
| Phase 5 | Apr 2026 | Buyer master data, enhanced serial tracking, PO accessories, rate limiting | 92% | 100% |
| Phase 6 | Apr 2026 | RBAC menu visibility, user-role assignment, PO buyer dropdown, WebSocket | 85% | 90% |
| **Phase 7** | **Apr 2026** | **PDF export: 16 types, PDF config module, all exports functional** | **100%** | **100%** |
| **Phase 8** | **Apr 2026** | **Bug fixes (continuation, serial, distribusi), dashboard overhaul, reminders** | **100%** | **100%** |

---

## 18. Known Issues & Remaining Items

### Resolved ✅ (v7–v8)
- PDF exports returning 400 "Unknown type" or blank content
- Child shipment items missing `po_item_id` linkage
- Available qty only counting original shipment (not additional/child)
- Distribusi kerja showing 0 diterima
- Serial tracking "belum dikirim" counting from produced instead of ordered
- Timeline events showing empty event/details
- Material request numbering not contextual
- Dashboard charts (work order, top garment) showing blank
- Dashboard notification panel too large
- Admin notes not visible in vendor portal

### Remaining 🔜
- [ ] Full RBAC enforcement middleware (permission checks per individual endpoint)
- [ ] Further backend modularization (split server.py into domain route files)
- [ ] Server-side pagination for heavy endpoints (distribusi-kerja, monitoring)
- [ ] Full Excel file upload import (currently JSON-based)
- [ ] Real-time WebSocket event broadcasting from business operations
- [ ] Mobile responsive polish (vendor/buyer portal sidebar toggle)
- [ ] Tighter CORS configuration for production
- [ ] Automated test suite
- [ ] PDF config: header/footer customization, column ordering, per-customer templates
- [ ] Vendor shipment multi-dispatch PDF (per dispatch + cumulative)

---

## 19. Future Implementation Recommendations

### 19.1 Short-Term Enhancements (1–3 months)

#### A. Advanced PDF System
- **Per-customer PDF templates**: Different PDF layouts per buyer (logo, terms, branding)
- **Configurable header/footer blocks**: Company logo, address, tax ID, bank details
- **Column ordering**: Drag-and-drop column arrangement in PDF config
- **Batch PDF export**: Download multiple PO/shipment PDFs as a single ZIP
- **PDF digital signatures**: Embed digital signature images for authenticated documents

#### B. Real-Time Notifications
- **WebSocket event broadcasting**: Push events to connected clients when:
  - Shipment status changes
  - Material request approved/rejected
  - Production progress milestones reached
  - Invoice payment received
- **Browser notifications**: Push notifications for urgent alerts
- **Email/SMS integration**: Optional email alerts for deadline reminders (SendGrid/Twilio)

#### C. Mobile Optimization
- **Progressive Web App (PWA)**: Installable vendor portal for mobile workers
- **Responsive sidebar toggle**: Collapsible mobile navigation for all portals
- **Touch-optimized inspection forms**: Large buttons, swipe actions for vendor portal
- **Barcode/QR scanning**: Camera-based serial number scanning for receiving and inspection

#### D. Advanced Analytics Dashboard
- **Vendor scorecards**: Quality rate, on-time delivery, defect history per vendor
- **Production forecasting**: ML-based prediction of delivery dates based on historical throughput
- **Cost variance analysis**: Actual vs budgeted cost per PO
- **Lead time analytics**: Average vendor lead time trends
- **Custom date range filters**: Week, month, quarter, YTD, custom
- **Export analytics as PDF/Excel**: One-click analytics report generation

---

### 19.2 Medium-Term Expansions (3–6 months)

#### E. Warehouse Management System (WMS)
**Purpose**: Track physical inventory locations, bin management, pick/pack/ship operations

```
┌─────────────────────────────────────────────────┐
│              WAREHOUSE MANAGEMENT                │
├─────────────────────────────────────────────────┤
│ • Warehouse/Location master data                │
│ • Bin/Shelf/Zone management                     │
│ • Inbound receiving (linked to vendor shipment) │
│ • Put-away operations                           │
│ • Stock transfer between locations              │
│ • Pick lists for buyer shipments                │
│ • Cycle counting / stock opname                 │
│ • Min/Max stock alerts                          │
│ • FIFO/LIFO tracking                            │
│ • Barcode label printing                        │
└─────────────────────────────────────────────────┘
```

**Integration with current ERP**:
- Vendor Shipment → WMS Inbound Receiving → Inspection → Put-away
- Buyer Shipment → WMS Pick List → Pack → Ship
- Serial Tracking → WMS Location History
- Dashboard → Real-time stock levels

**New Collections**: `warehouses`, `warehouse_zones`, `warehouse_bins`, `inventory_movements`, `stock_levels`, `pick_lists`, `cycle_counts`

#### F. Supply Chain Management (SCM)
**Purpose**: Manage raw material procurement, supplier relationships, and logistics

```
┌─────────────────────────────────────────────────┐
│             SUPPLY CHAIN MANAGEMENT              │
├─────────────────────────────────────────────────┤
│ • Raw Material Catalog (fabrics, threads, etc.) │
│ • Bill of Materials (BOM) per product           │
│ • Material Requirements Planning (MRP)          │
│ • Purchase Requisitions → Purchase Orders       │
│ • Supplier management & evaluation              │
│ • Incoming quality inspection                   │
│ • Material consumption tracking                 │
│ • Reorder point alerts                          │
│ • Landed cost calculation                       │
│ • Supplier lead time analysis                   │
└─────────────────────────────────────────────────┘
```

**Integration with current ERP**:
- Product → BOM → Material Requirements
- PO created → Auto-generate raw material purchase requisitions
- Vendor evaluation → Quality scores from inspection data
- Cost tracking → Actual material cost flows to financial recap

**New Collections**: `raw_materials`, `bill_of_materials`, `bom_items`, `purchase_requisitions`, `material_consumption`, `supplier_evaluations`

#### G. Quality Management System (QMS)
**Purpose**: Formalize quality processes, track defect patterns, enforce quality gates

```
┌─────────────────────────────────────────────────┐
│            QUALITY MANAGEMENT SYSTEM             │
├─────────────────────────────────────────────────┤
│ • Quality standards & checklists per product    │
│ • Inspection templates (AQL-based sampling)     │
│ • Defect category taxonomy                      │
│ • Corrective Action Requests (CAR)              │
│ • Root Cause Analysis (RCA) tracking            │
│ • Quality gates (hold production until pass)    │
│ • Supplier quality ratings                      │
│ • Quality cost tracking (rework, scrap, return) │
│ • Statistical Process Control (SPC) charts      │
│ • Quality certificates & compliance docs        │
└─────────────────────────────────────────────────┘
```

**Integration with current ERP**:
- Material Inspection → QMS checklist validation
- Defect Reports → CAR generation
- Production Returns → RCA tracking
- Vendor Scorecard → Quality rating component
- Dashboard → Quality KPIs (defect rate, first-pass yield)

---

### 19.3 Long-Term Vision (6–12 months)

#### H. Customer Relationship Management (CRM)
- **Buyer profiles**: Communication history, order patterns, preferences
- **Quote management**: Create, send, and track price quotations
- **Order pipeline**: Visual Kanban of buyer orders from inquiry to delivery
- **Buyer satisfaction surveys**: Post-delivery feedback collection
- **Revenue forecasting**: Predict revenue based on pipeline and historical data

#### I. Human Resources Module (HR)
- **Worker profiles**: Skills, certifications, productivity metrics
- **Attendance & shift management**: Clock in/out, overtime tracking
- **Piece-rate pay calculation**: Link production progress to worker compensation
- **Training records**: Track worker skill development
- **Capacity planning**: Match workforce availability to production demand

#### J. Business Intelligence & Reporting Engine
- **Custom report builder**: Drag-and-drop report designer
- **Scheduled reports**: Auto-generate and email reports on schedule
- **Cross-module analytics**: Combine production, financial, quality, and logistics data
- **Executive summary PDF**: One-page business overview with key metrics
- **Data export to BI tools**: API for Tableau, Power BI, Metabase integration

#### K. Multi-Company & Multi-Currency
- **Multi-company support**: Separate P&L per business entity
- **Multi-currency invoicing**: Support USD, EUR, etc. with exchange rate management
- **Inter-company transfers**: Track material/financial flows between entities
- **Consolidated reporting**: Group-level financial overview

#### L. AI/ML Integration
- **Demand forecasting**: Predict order volumes based on seasonal patterns
- **Anomaly detection**: Flag unusual production metrics or financial transactions
- **Optimal vendor allocation**: ML-based vendor selection for new POs based on quality, cost, lead time
- **Natural language search**: AI-powered search across all modules ("show me overdue POs for vendor X")
- **Document OCR**: Extract data from scanned purchase orders, invoices, delivery notes

---

### 19.4 Infrastructure Recommendations

| Area | Current State | Recommended Upgrade |
|------|--------------|---------------------|
| Backend structure | Single `server.py` (4,540 lines) | Split into domain routers: `routes/po.py`, `routes/shipments.py`, etc. |
| Database | No pagination | Server-side cursor pagination with `skip`/`limit` |
| Auth | JWT with role check | Full RBAC middleware per-endpoint |
| Testing | Manual + testing agent | Automated pytest suite with CI/CD |
| Deployment | Kubernetes single pod | Multi-replica with load balancer |
| Cache | None | Redis cache for dashboard aggregations |
| Search | Simple regex | Elasticsearch/Meilisearch for full-text search |
| File storage | Emergent Object Storage | CDN for file delivery + image optimization |
| Monitoring | Supervisor logs | Prometheus + Grafana for metrics |
| CORS | Open (`*`) | Strict origin whitelist |
| API docs | None | OpenAPI/Swagger auto-docs from FastAPI |

---

## 20. Appendix

### Credentials (Development)

| Role | Email | Password |
|------|-------|----------|
| Superadmin | admin@garment.com | Admin@123 |
| Vendor | vendor.[code]@garment.com | Auto-generated (see Data Vendor) |
| Buyer | buyer.[code]@garment.com | Auto-generated (see Data Buyer) |

### Key Design Decisions

1. **UUID over ObjectID** — JSON serialization, frontend-friendly
2. **po_item_id as matching key** — Prevents data conflicts with duplicate visible fields
3. **Three separate portals** — Role-based routing at login (ERP/Vendor/Buyer)
4. **Staged PO lifecycle** — No auto-close; explicit status transitions
5. **Append-only documentation** — New phases appended, never replaced
6. **Buyer master data mirrors vendor pattern** — Auto-create account, dropdown in PO
7. **Accessories parallel to main material** — Same request→approval→child-shipment pattern
8. **Continuation aggregation from PO items** — All shipments (parent+child) aggregate via `po_item_id` (v8)
9. **Interactive dashboard** — KPI cards open drilldown modals for detailed context (v8)
10. **Reminder system bi-directional** — ERP sends, vendor responds, creating accountability trail (v8)
11. **PDF config presets** — Column selection per PDF type with default system (v7)

---

*This document is maintained alongside the codebase and updated with each development phase.*

**Author:** Development Team  
**Version:** 8.0
