"""Reference data & business constants for RCG Digital Restructuring."""

RCG_CAP = 30_000_000_000  # 30 Miliar (limit maksimal RCG / IMMADHA)
RATMIYATI_CAP = 10_000_000_000  # 10 Miliar (limit pemutus RATMIYATI di level RCG)
IMMADHA_NIP = "2175007386"
RATMIYATI_NIP = "2180007674"
# Satu-satunya NIP yang berhak mengelola user (SYAMSU RIZAL)
USER_ADMIN_NIP = "2183008345"

# Master RCG users (from problem statement)
RCG_USERS = [
    {"nip": "2175007386", "nama": "IMMADHA HANDY KUSUMA", "jabatan": "Group Head Retail Collection, Restructuring & Recovery Group", "limit_pemutus": 30_000_000_000, "can_approve": True, "is_user_admin": False},
    {"nip": "2180007674", "nama": "RATMIYATI", "jabatan": "RCG", "limit_pemutus": 10_000_000_000, "can_approve": True, "is_user_admin": False},
    {"nip": "2183008345", "nama": "SYAMSU RIZAL", "jabatan": "RCG", "limit_pemutus": 0, "can_approve": False, "is_user_admin": True},
    {"nip": "2182008560", "nama": "Rizqy Rafiq Ahmad", "jabatan": "Micro Midrange & NPF Manager", "limit_pemutus": 0, "can_approve": False, "is_user_admin": False},
    {"nip": "2180005430", "nama": "Irfan Misbahul Arif", "jabatan": "SME Midrange & NPF Manager", "limit_pemutus": 0, "can_approve": False, "is_user_admin": False},
    {"nip": "2182001318", "nama": "Egy Aprianto", "jabatan": "Consumer Midrange & NPF Manager", "limit_pemutus": 0, "can_approve": False, "is_user_admin": False},
    {"nip": "2182008108", "nama": "Eka Buana Garbawati", "jabatan": "SME & Micro Collection Department Head", "limit_pemutus": 0, "can_approve": False, "is_user_admin": False},
]

JABATAN = {
    "RCO": "Retail Collection, Restructuring & Recovery Officer",
    "ACRM": "Area Retail Collection, Restructuring & Recovery Manager",
    "RCRM": "Area Regional Collection, Restructuring & Recovery Manager",
    "RCG": "Retail Collection, Restructuring & Recovery Group",
}

KOLEKTIBILITAS = ["2A", "2B", "2C", "3A", "3B", "3C", "4A", "4B", "4C", "5"]

SEGMEN = ["KONSUMER", "RETAIL"]

PRODUK = {
    "KONSUMER": ["Griya", "Mitraguna", "Pensiunan", "Pra Pensiunan", "Cicil Emas"],
    "RETAIL": ["SME", "Mikro"],
}

AKAD = {
    "KONSUMER": ["Murabahah", "MMQ", "Musyarakah", "Rahn"],
    "RETAIL": ["Murabahah", "Musyarakah", "MMQ", "Ijarah"],
}

KEPADA = ["ACRM", "RCRM", "GH RCG"]

PENILAI_JAMINAN = ["Internal (AFO/RFO)", "KJPP"]

KEMAMPUAN_BAYAR = [
    "Terdapat bukti pendapatan nasabah/slip gaji",
    "Terdapat laporan keuangan usaha nasabah",
]

RAC_KONSUMER = [
    "Terdapat surat permohonan restrukturisasi dari nasabah",
    "Nasabah mengalami penurunan kemampuan membayar",
    "Terdapat Informasi Debitur (iDeb) untuk mengetahui track record pembiayaan nasabah di tempat lain serta mendukung analisis kemampuan membayar dan karakter nasabah",
    "Terdapat penghasilan atau sumber pembayaran angsuran yang jelas, baik dari nasabah maupun sumber lain yang sah, sehingga nasabah dinilai mampu memenuhi kewajibannya setelah restrukturisasi",
    "Nasabah tidak termasuk nasabah fraud berdasarkan hasil audit internal dan/atau eksternal",
]

RAC_RETAIL = [
    "Karakter = Kooperatif dan memiliki itikad baik",
    "Usaha = Masih berjalan minimal 6 bulan terakhir",
    "Kemampuan Bayar = Mampu membayar angsuran baru dari cash flow",
    "Agunan = Legal dan marketable",
    "Prospek = Terdapat potensi pemulihan usaha",
    "Fraud = Tidak terindikasi fraud",
    "Legalitas = Dokumen lengkap dan valid",
    "Outcome Restrukturisasi = Diperkirakan memperbaiki kualitas pembiayaan",
]

DOCUMENT_TYPES = [
    {"key": "foto_ots", "label": "Foto pertemuan pihak bank dengan nasabah / OTS", "required": True},
    {"key": "surat_permohonan_ktp", "label": "Surat Permohonan Nasabah + KTP Nasabah", "required": True},
    {"key": "laporan_agunan", "label": "Laporan Penilaian Agunan", "required": False, "required_if_fix_asset": True},
    {"key": "bi_checking", "label": "BI Checking / iDeb Nasabah", "required": True},
]

SYARAT_AKAD = [
    "Nasabah telah mengajukan surat permohonan restrukturisasi",
    "Nasabah telah menandatangani Surat Persetujuan restrukturisasi",
    "Nasabah telah menandatangani komitmen pembayaran sesuai dengan tabel/jadwal angsuran restrukturisasi",
    "Lainnya sesuai dengan ketentuan pembiayaan dan restrukturisasi di PT. Bank Syariah Indonesia, Tbk.",
]

LAINNYA = [
    "Source of Payment Capacity harus jelas dan mengcover angsuran nasabah",
    "Jika nasabah ingin melakukan pelunasan dipercepat maka harus mengacu kepada tabel angsuran yang pertama dan sesuai dengan ketentuan PT. Bank Syariah Indonesia, Tbk.",
]

LAINNYA_PELANGGARAN = "Apabila terjadi pelanggaran-pelanggaran tersebut di atas, maka Bank dapat menarik kembali secara sekaligus atas fasilitas yang diberikan, melalui penjualan jaminan ataupun upaya penagihan lainnya menurut aturan hukum atau norma yang berlaku."

PENUTUP = ["Demikian kami sampaikan, mohon keputusan dari Komite Pembiayaan.", "Wassalaamu'alaikum Wr. Wb"]

KARAKTER_TEXT = "Nasabah masih memiliki karakter yang baik dibukti dengan permohonan pengajuan restruktur ke pihak bank yang membuktikan nasabah masih memiliki itikad baik untuk menyelesaikan kewajibannya di bank."

APPROVED_KETERANGAN = "Nota ini telah dikomitekan oleh pengusul dan telah DISETUJUI oleh pemutus sesuai limit kewenangan memutus melalui aplikasi internal RCG (PT. Bank Syariah Indonesia, Tbk), tanda Approved muncul otomatis jadi tidak perlu tandatangan basah/digital"

DARI = "Retail Collection, Restructuring & Recovery Officer"

PEMBUKA = ["Wassalaamu'alaikum Wr. Wb", "Dengan ini kami sampaikan Nota Analisa Restruktur Pembiayaan sebagai berikut:"]
