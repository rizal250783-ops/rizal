# PRD — CASEWISE LEGAL PERDATA
## PT. BANK SYARIAH INDONESIA, Tbk

### Problem Statement (ringkasan)
Legal Case Management System internal untuk Legal Group (LGG) BSI: monitoring, pengelolaan, approval (maker-checker), dokumentasi PDF, dashboard KPI, laporan, dan database management perkara gugatan perdata. Bahasa Indonesia. Warna brand: Hijau Toska #00a0a0, Gold #f0b43c.

### Catatan Teknologi
- Spesifikasi meminta Node.js; environment Emergent menggunakan **FastAPI + React + MongoDB** (standar platform) — fungsionalitas identik.
- Database: MongoDB internal (MONGO_URL dari env).

### User Persona
1. **Legal Litigation & Advice Officer** (role key: admin_legal) — input/edit/hapus (via approval), upload dokumen, agenda sidang, export Excel, monitoring. Pejabat: Maya Dewi Maharani (admin), Arsya Daniswara Dwitama (arsya).
2. **Legal Litigation & Advice Manager** (role key: dept_head) — approve/reject semua perubahan, user management, database management, KPI management. Pejabat: Teguh Sutadi (depthead).

### Akun Seed
- depthead / DeptHead2026! — Teguh Sutadi (LLA Manager, email: rizal.250783@gmail.com)
- admin / Admin2026! — Maya Dewi Maharani (LLA Officer)
- arsya / Arsya2026! — Arsya Daniswara Dwitama (LLA Officer)
- Label jabatan di seluruh UI: "Legal Litigation & Advice Manager" / "Legal Litigation & Advice Officer" (badge: LLA Manager / LLA Officer).
- (26 Agu 2026) Database perkara dikosongkan atas permintaan user (12 perkara contoh + 61 approval + 11 export log dihapus, file upload dibersihkan); seed data contoh dinonaktifkan di server.py. Akun user tetap dipertahankan.
- (26 Agu 2026) Istilah unit diganti: "Legal Group (LGG)" → "Retail Collection, Restructuring & Recovery Group (RCG)" di halaman login & dashboard.

### Yang Sudah Diimplementasikan (25 Agu 2026)
- Dropdown bertingkat Region → Area berdasarkan file master "NAMA REGION DAN NAMA AREA.xlsx" (12 Region / RO, 45 Area, mapping di /app/backend/region_area.json, diekspos via GET /api/master-data field region_area_map). Memilih region otomatis memfilter opsi area di form Input/Edit Perkara (tab Organisasi BSI) dan filter Area di Dashboard, Data Perkara, Laporan, Database Management (ganti region mereset filter area).
- Logo resmi PT. Bank Syariah Indonesia (file /app/frontend/public/bsi-logo.png) terpasang di halaman login (panel hero + kartu login), sidebar dashboard, dan header mobile.
- Auth JWT username/password + brute-force lockout (5x gagal → 423, kunci 15 menit; password benar membuka kembali).
- Dashboard: KPI (perkara aktif, total kewajiban Rp, region/area/cabang, pending approval), grid 13 tahap proses, bar chart per region, pie chart status, area chart perjalanan perkara, panel Reminder & Tenggat (hari tersisa), filter tahun/region/area/cabang/status.
- Data Perkara: tabel + search (nomor/penggugat/tergugat/CIF/loan) + filter lengkap + export Excel.
- Form multi-tab: Informasi Perkara (penggugat/tergugat dinamis), Organisasi BSI, CIF & Loan dinamis (1 CIF banyak loan, total kewajiban otomatis), Jaminan dinamis, Mediasi, Risk Rating + rekomendasi.
- Approval workflow maker-checker: CREATE/EDIT/DELETE_NONAKTIF/DELETE_PERMANENT → MENUNGGU → APPROVED/REJECTED (reject wajib alasan, kolom approver/tanggal/catatan). Re-validasi duplikat nomor perkara saat approve (400, bukan 500).
- Detail perkara: tab Detail, Agenda Sidang (otomatis masuk timeline), Dokumen (17 kategori, upload PDF only, preview/download/delete), Timeline vertikal, Status & Risk (18 tahapan status).
- Halaman Timeline Perkara, Dokumen Perkara (global), Laporan (9 jenis termasuk aging 0-3/3-6/6-12/>12 bulan & executive summary), Master Data.
- User Management (dept head): tambah admin, aktif/nonaktif; user nonaktif tidak bisa login; menu tersembunyi untuk admin.
- Database Management (dept head): export database multi-sheet (6 sheet) dengan filter + aktif-only, info backup terakhir, download template import (4 sheet), import dengan validasi (sheet/baris/kolom/keterangan error), preview (baru/update/gagal) → LANJUTKAN/BATALKAN.
- Seed 12 data perkara contoh (8 region, berbagai status/tahun/risk).
- Role guard frontend + backend (403) untuk /users, /database, /api/users, /api/export/database, /api/import/*.

### Status Pengujian
- Backend: 49/49 pytest lulus (/app/backend/tests/backend_test.py).
- Frontend: seluruh alur utama diverifikasi Playwright (testing agent iterasi 1) + screenshot manual.
- Perbaikan pasca-test: duplikat nomor perkara saat approve (HIGH), brute-force lockout, CORS credentials, validasi import (non-numerik → baris error, batas 10MB), seed idempoten, 404 agenda delete, a11y SheetTitle.

### Backlog Prioritas
- P1: Ganti input date native dengan shadcn Calendar (format dd/mm/yyyy); hapus warning Recharts width(-1).
- P2: Notifikasi in-app untuk admin saat request di-approve/reject; pagination server-side untuk tabel besar; pecah server.py menjadi modul (auth, cases, approvals, documents, export/import).
- P2: Audit trail opsional (spesifikasi awal mengecualikan); hard-delete user.
