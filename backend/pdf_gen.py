"""Professional printable PDF generation for approved notes."""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

TEAL = colors.HexColor("#00A0A0")
GOLD = colors.HexColor("#F0B43C")
DARK = colors.HexColor("#0F172A")
LIGHT = colors.HexColor("#F1F5F9")


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


def generate_note_pdf(note: dict) -> bytes:
    ss = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=15 * mm, bottomMargin=18 * mm, leftMargin=15 * mm, rightMargin=15 * mm)
    el = []

    _nomor = note.get("nomor_nota", "") or "-"
    _status = note.get("status", "") or ""

    def _decorate(canvas, doc_):
        canvas.saveState()
        w, h = A4
        # footer separator
        canvas.setStrokeColor(GOLD)
        canvas.setLineWidth(0.8)
        canvas.line(15 * mm, 12 * mm, w - 15 * mm, 12 * mm)
        canvas.setFont("Helvetica", 6.5)
        canvas.setFillColor(colors.grey)
        canvas.drawString(15 * mm, 8 * mm, "DOKUMEN RAHASIA - PT. Bank Syariah Indonesia, Tbk (Internal Use Only)")
        canvas.drawCentredString(w / 2, 8 * mm, f"Nota: {_nomor}")
        canvas.drawRightString(w - 15 * mm, 8 * mm, f"Halaman {doc_.page}")
        canvas.restoreState()

    # Header
    head = Table([[
        Paragraph("<b>BSI</b>  BANK SYARIAH INDONESIA", ParagraphStyle("hd", fontName="Helvetica-Bold", fontSize=13, textColor=TEAL)),
        Paragraph("RCG DIGITAL RESTRUCTURING<br/><font size=7 color='#F0B43C'>Solusi cerdas menuju pembiayaan berkelanjutan</font>", ParagraphStyle("hd2", fontName="Helvetica", fontSize=8, textColor=DARK, alignment=2)),
    ]], colWidths=[100 * mm, 80 * mm])
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

    doc.build(el, onFirstPage=_decorate, onLaterPages=_decorate)
    buf.seek(0)
    return buf.read()
