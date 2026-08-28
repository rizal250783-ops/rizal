"""Professional printable PDF generation for approved notes."""
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether, Image,
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfgen import canvas as _canvas

TEAL = colors.HexColor("#00A0A0")
GOLD = colors.HexColor("#F0B43C")
DARK = colors.HexColor("#0F172A")
LIGHT = colors.HexColor("#F1F5F9")

LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "bsi_logo.png")


class NumberedCanvas(_canvas.Canvas):
    """Canvas dua-lintasan untuk menomori halaman: 'Halaman X dari Y halaman'."""

    def __init__(self, *args, **kwargs):
        self._nomor = kwargs.pop("nomor", "-")
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for i, state in enumerate(self._saved_page_states, 1):
            self.__dict__.update(state)
            self._draw_footer(i, total)
            super().showPage()
        super().save()

    def _draw_footer(self, page_num, total):
        w, h = A4
        self.saveState()
        self.setStrokeColor(GOLD)
        self.setLineWidth(0.8)
        self.line(15 * mm, 12 * mm, w - 15 * mm, 12 * mm)
        self.setFont("Helvetica", 6.5)
        self.setFillColor(colors.grey)
        self.drawString(15 * mm, 8 * mm, "DOKUMEN RAHASIA - PT. Bank Syariah Indonesia, Tbk (Internal Use Only)")
        self.drawCentredString(w / 2, 8 * mm, f"Nota: {self._nomor}")
        self.drawRightString(w - 15 * mm, 8 * mm, f"Halaman {page_num} dari {total} halaman")
        self.restoreState()


def _logo_flowable():
    """Logo BSI (pojok kanan atas). Fallback ke teks jika file logo belum tersedia."""
    if os.path.exists(LOGO_PATH):
        try:
            img = Image(LOGO_PATH)
            iw, ih = img.imageWidth, img.imageHeight
            target_h = 14 * mm
            img.drawHeight = target_h
            img.drawWidth = iw * (target_h / ih)
            img.hAlign = "RIGHT"
            return img
        except Exception:
            pass
    return Paragraph(
        "RCG DIGITAL RESTRUCTURING<br/><font size=7 color='#F0B43C'>Solusi cerdas menuju pembiayaan berkelanjutan</font>",
        ParagraphStyle("hd2", fontName="Helvetica", fontSize=8, textColor=DARK, alignment=TA_RIGHT),
    )


def rp(v):
    try:
        return "Rp" + f"{int(round(float(v or 0))):,}".replace(",", ".")
    except Exception:
        return "Rp0"


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("Title2", fontName="Helvetica-Bold", fontSize=14, textColor=TEAL, spaceAfter=2))
    ss.add(ParagraphStyle("Sub", fontName="Helvetica", fontSize=8, textColor=colors.grey))
    ss.add(ParagraphStyle("SecHead", fontName="Helvetica-Bold", fontSize=10, textColor=colors.white, spaceBefore=8, spaceAfter=4))
    ss.add(ParagraphStyle("Body2", fontName="Helvetica", fontSize=8.5, textColor=DARK, leading=12, alignment=TA_JUSTIFY))
    ss.add(ParagraphStyle("Small", fontName="Helvetica", fontSize=7.5, textColor=DARK, leading=10))
    ss.add(ParagraphStyle("SmallB", fontName="Helvetica-Bold", fontSize=7.5, textColor=DARK, leading=10))
    ss.add(ParagraphStyle("SmallW", fontName="Helvetica-Bold", fontSize=7.5, textColor=colors.white, leading=10))
    return ss


def _section(title, ss):
    t = Table([[Paragraph(title, ss["SecHead"])]], colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TEAL),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def _kv(rows, ss, widths=(45 * mm, 135 * mm)):
    data = [[Paragraph(str(k), ss["SmallB"]), Paragraph(str(v), ss["Small"])] for k, v in rows]
    t = Table(data, colWidths=list(widths))
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def _grid(header, rows, ss, widths):
    data = [[Paragraph(h, ss["SmallW"]) for h in header]]
    for r in rows:
        data.append([Paragraph(str(c), ss["Small"]) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]
    t.setStyle(TableStyle(style))
    return t


def _block(title, flowables, ss):
    """Section header + its content kept together to avoid orphaned headers."""
    items = [_section(title, ss)]
    items.extend(flowables if isinstance(flowables, list) else [flowables])
    return KeepTogether(items)


def _sign_column(cells, ss):
    t = Table([[c] for c in cells])
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def _signatures(note, ss):
    """Kolom tanda tangan basah/digital: Pengusul (I, II, III...) + Pemutus.
    Disposisi pemutus diletakkan sejajar dalam kolom pemutus."""
    st_title = ParagraphStyle("sgT", fontName="Helvetica-Bold", fontSize=8, textColor=DARK, alignment=TA_CENTER, leading=11)
    st_sub = ParagraphStyle("sgS", fontName="Helvetica", fontSize=7.5, textColor=DARK, alignment=TA_CENTER, leading=10)
    st_name = ParagraphStyle("sgN", fontName="Helvetica-Bold", fontSize=8, textColor=DARK, alignment=TA_CENTER, leading=11)
    st_disp = ParagraphStyle("sgD", fontName="Helvetica-Oblique", fontSize=7, textColor=DARK, alignment=TA_CENTER, leading=9)

    approvals = note.get("approvals", [])
    pengusul = [ap for ap in approvals if ap.get("fungsi") == "Pengusul"]
    if not pengusul:
        pengusul = [{"nama": note.get("creator_nama", ""), "nip": note.get("creator_nip", ""),
                     "jabatan": note.get("creator_jabatan") or note.get("dari", "")}]
    labels = ["Pengusul I", "Pengusul II", "Pengusul III", "Pengusul IV", "Pengusul V"]
    n = len(pengusul)

    columns = []
    for i, p in enumerate(pengusul):
        title = labels[i] if n > 1 else "Pengusul"
        columns.append(_sign_column([
            Paragraph(title, st_title),
            Paragraph(p.get("jabatan") or "", st_sub),
            Spacer(1, 22 * mm),
            Paragraph(p.get("nama") or "", st_name),
            Paragraph(f"NIP {p.get('nip') or ''}", st_sub),
        ], ss))

    disposisi = (note.get("disposisi_pemutus") or "").strip()
    pemutus_cells = [
        Paragraph("Pemutus", st_title),
        Paragraph(note.get("final_approver_jabatan") or "", st_sub),
    ]
    if disposisi:
        pemutus_cells.append(Paragraph(f"Disposisi: {disposisi}", st_disp))
        pemutus_cells.append(Spacer(1, 14 * mm))
    else:
        pemutus_cells.append(Spacer(1, 22 * mm))
    pemutus_cells += [
        Paragraph(note.get("final_approver_nama") or "", st_name),
        Paragraph(f"NIP {note.get('final_approver_nip') or ''}", st_sub),
    ]
    columns.append(_sign_column(pemutus_cells, ss))

    total_cols = len(columns)
    cw = (180 * mm) / total_cols
    grid = Table([columns], colWidths=[cw] * total_cols)
    grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return KeepTogether([
        _section("TANDA TANGAN PENGUSUL & PEMUTUS", ss),
        Spacer(1, 2),
        grid,
    ])


def generate_note_pdf(note: dict) -> bytes:
    ss = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=15 * mm, bottomMargin=18 * mm, leftMargin=15 * mm, rightMargin=15 * mm)
    el = []

    _nomor = note.get("nomor_nota", "") or "-"
    _status = note.get("status", "") or ""

    # Header: judul aplikasi (kiri) + logo BSI (kanan atas)
    head = Table([[
        Paragraph("RCG DIGITAL RESTRUCTURING<br/><font size=7 color='#F0B43C'>Solusi cerdas menuju pembiayaan berkelanjutan</font>", ParagraphStyle("hd", fontName="Helvetica-Bold", fontSize=12, textColor=TEAL, leading=15)),
        _logo_flowable(),
    ]], colWidths=[110 * mm, 70 * mm])
    head.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    el.append(head)
    el.append(HRFlowable(width="100%", thickness=1.5, color=GOLD, spaceBefore=4, spaceAfter=6))
    el.append(Paragraph("NOTA ANALISA RESTRUKTUR PEMBIAYAAN", ParagraphStyle("c", fontName="Helvetica-Bold", fontSize=11, textColor=DARK, alignment=TA_CENTER, spaceAfter=6)))

    c = note.get("customer", {})
    el.append(_kv([
        ("Nomor Nota", note.get("nomor_nota", "")),
        ("Dari", note.get("dari", "")),
        ("Tanggal", note.get("tanggal_nota", "")),
        ("Pemutus", note.get("kepada", "")),
        ("Reff", f"Surat Permohonan Nasabah tanggal {note.get('reff_tanggal','-')}"),
        ("Perihal", note.get("perihal", "")),
    ], ss))
    el.append(Spacer(1, 4))
    for p in note.get("pembuka", []):
        el.append(Paragraph(p, ss["Body2"]))

    # Customer
    el.append(_section("INFORMASI NASABAH", ss))
    el.append(_kv([
        ("Nama Nasabah", c.get("nama", "")),
        ("Alamat", c.get("alamat", "")),
        ("No. Kontak", c.get("no_kontak", "")),
        ("Restrukturisasi ke", c.get("restrukturisasi_ke", "")),
    ], ss))

    # Facilities
    el.append(_section("FASILITAS PEMBIAYAAN EXISTING", ss))
    fac_rows = []
    for f in note.get("facilities", []):
        fac_rows.append([
            f.get("nama_cabang", ""), f.get("cif", ""), f.get("nomor_loan", ""), f.get("kolektibilitas", ""),
            f"{f.get('segmen','')}/{f.get('produk','')}", f.get("akad", ""),
            rp(f.get("os_pokok")), rp(f.get("os_margin")), rp(f.get("penalty")), rp(f.get("total_kewajiban")),
        ])
    el.append(_grid(
        ["Cabang", "CIF", "No Loan", "Kol", "Segmen/Produk", "Akad", "OS Pokok", "OS Margin", "Penalty", "Total"],
        fac_rows, ss,
        [24 * mm, 14 * mm, 16 * mm, 8 * mm, 24 * mm, 16 * mm, 18 * mm, 18 * mm, 16 * mm, 18 * mm],
    ))
    el.append(Spacer(1, 3))
    el.append(_kv([
        ("Total Outstanding Pokok + Tunggakan Pokok", rp(note.get("total_os_pokok"))),
        ("Total Outstanding Margin + Tunggakan Margin", rp(note.get("total_os_margin"))),
        ("Total Penalty", rp(note.get("total_penalty"))),
        ("Total Kewajiban", rp(note.get("total_kewajiban"))),
    ], ss))

    # Collateral
    el.append(_section("AGUNAN / JAMINAN", ss))
    if note.get("has_fix_asset") and note.get("collaterals"):
        crows = []
        for col in note["collaterals"]:
            _pen = col.get("penilai", "")
            if _pen == "KJPP" and col.get("nama_kjpp"):
                _pen = f"KJPP - {col.get('nama_kjpp')}"
            crows.append([col.get("jenis", ""), rp(col.get("nilai_pasar")), rp(col.get("nilai_likuidasi")),
                          f"{col.get('ccr_pasar',0):.1f}%", f"{col.get('ccr_likuidasi',0):.1f}%", _pen])
        el.append(_grid(["Jenis", "Nilai Pasar", "Nilai Likuidasi", "CCR Pasar", "CCR Likuidasi", "Penilai"], crows, ss,
                        [40 * mm, 28 * mm, 28 * mm, 22 * mm, 24 * mm, 28 * mm]))
    else:
        el.append(Paragraph("Tidak ada jaminan fix asset", ss["Body2"]))

    # RAC
    el.append(_section("RISK ACCEPTANCE CRITERIA (RAC)", ss))
    rrows = [[r.get("parameter", ""), r.get("status", ""), r.get("keterangan", "") or "-"] for r in note.get("rac", [])]
    el.append(_grid(["Parameter", "Status", "Keterangan"], rrows, ss, [95 * mm, 30 * mm, 55 * mm]))

    if note.get("ra_required"):
        el.append(_section("RISK ASSESSMENT (FRA UNIT)", ss))
        el.append(Paragraph(f"Status: {note.get('risk_assessment',{}).get('status','Belum dilakukan')}", ss["Body2"]))

    # Analysis
    a = note.get("analysis", {})
    el.append(_section("ANALISA", ss))
    el.append(_kv([
        ("Profil Nasabah / Kondisi Usaha", a.get("profil", "Terpenuhi")),
        ("Informasi Karakter", a.get("karakter", "")),
        ("Penyebab Nasabah Bermasalah", a.get("penyebab_bermasalah", "")),
        ("Kemampuan Bayar", a.get("kemampuan_bayar", "")),
        ("Informasi Jaminan & CCR", a.get("informasi_jaminan", "")),
        ("TBO", a.get("tbo", "Terpenuhi, tidak ada TBO")),
    ], ss))

    # Proposals
    el.append(_section("USULAN RESTRUKTURISASI", ss))
    el.append(Paragraph(note.get("usulan_kalimat", ""), ss["Body2"]))
    el.append(Spacer(1, 3))
    prows = []
    for p in note.get("proposals", []):
        prows.append([p.get("jenis_fasilitas", ""), p.get("akad", ""), p.get("tujuan", ""),
                      rp(p.get("os_pokok")), rp(p.get("os_margin")),
                      f"{p.get('tgl_mulai','')} s/d {p.get('tgl_akhir','')} ({p.get('durasi','')})"])
    el.append(_grid(["Jenis Fasilitas", "Akad", "Tujuan", "OS Pokok", "OS Margin", "Jangka Waktu"], prows, ss,
                    [24 * mm, 20 * mm, 26 * mm, 24 * mm, 24 * mm, 42 * mm]))

    # Syarat + lainnya
    el.append(_section("SYARAT-SYARAT PENANDATANGANAN AKAD", ss))
    for i, s in enumerate(note.get("syarat_akad", []), 1):
        el.append(Paragraph(f"{i}. {s}", ss["Small"]))
    el.append(_section("LAINNYA", ss))
    for i, s in enumerate(note.get("lainnya", []), 1):
        el.append(Paragraph(f"{i}. {s}", ss["Small"]))
    if note.get("lainnya_pelanggaran"):
        el.append(Spacer(1, 2))
        el.append(Paragraph(note["lainnya_pelanggaran"], ss["Body2"]))
    el.append(Spacer(1, 3))
    for p in note.get("penutup", []):
        el.append(Paragraph(p, ss["Body2"]))

    # Disposisi Pemutus
    if note.get("disposisi_pemutus"):
        el.append(_section("DISPOSISI PEMUTUS", ss))
        el.append(Paragraph(note.get("disposisi_pemutus", ""), ss["Body2"]))

    # Approval history
    el.append(_section("RIWAYAT PERSETUJUAN", ss))
    arows = []
    for ap in note.get("approvals", []):
        arows.append([f"{ap.get('nama','')} ({ap.get('role','')})", ap.get("jabatan", ""), ap.get("fungsi", ""),
                      ap.get("keputusan", ""), f"{ap.get('date','')} {ap.get('time','')}"])
    el.append(_grid(["User", "Jabatan", "Fungsi", "Keputusan", "Waktu"], arows, ss,
                    [40 * mm, 45 * mm, 25 * mm, 30 * mm, 40 * mm]))

    # Pengusul & Pemutus + Approved stamp (kept together)
    stamp = Table([[Paragraph("<b>APPROVED</b>", ParagraphStyle("st", fontName="Helvetica-Bold", fontSize=18, textColor=colors.white, alignment=TA_CENTER)),
                    Paragraph(f"Tanggal Approved: {note.get('approved_date','')}", ParagraphStyle("st2", fontName="Helvetica", fontSize=9, textColor=colors.white, alignment=TA_CENTER))]],
                   colWidths=[90 * mm, 90 * mm])
    stamp.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#10B981")), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    el.append(KeepTogether([
        _section("INFORMASI PENGUSUL & PEMUTUS", ss),
        _kv([
            ("Pengusul", f"{note.get('creator_nama','')} - NIP {note.get('creator_nip','')} ({note.get('dari','')})"),
            ("Pemutus", f"{note.get('final_approver_nama','')} - NIP {note.get('final_approver_nip','')}"),
            ("Jabatan Pemutus", note.get("final_approver_jabatan", "")),
            ("Level Pemutus", note.get("final_approver_level", "")),
            ("Limit Pemutus Digunakan", rp(note.get("limit_pemutus_used"))),
            ("Tanggal & Jam Approved", f"{note.get('approved_date','')} {note.get('approved_time','')}"),
        ], ss),
        Spacer(1, 6),
        stamp,
        Spacer(1, 4),
        Paragraph(note.get("approved_keterangan", ""), ParagraphStyle("kt", fontName="Helvetica-Oblique", fontSize=8, textColor=colors.grey, alignment=TA_JUSTIFY)),
    ]))

    # Kolom tanda tangan basah/digital (Pengusul I/II/III + Pemutus) — hanya untuk nota approved
    if note.get("status") == "Final Approved" or note.get("final_approver_nama"):
        el.append(Spacer(1, 6))
        el.append(_signatures(note, ss))

    doc.build(el, canvasmaker=lambda *a, **k: NumberedCanvas(*a, nomor=_nomor, **k))
    buf.seek(0)
    return buf.read()
