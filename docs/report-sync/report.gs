/**
 * ProofSkill: brings the D1+D2 report in line with the deployed website and adds Deliverable 3.
 * Runs from a standalone Apps Script project and opens the report by ID. Run dryRun() first; it changes nothing
 * and logs every find that does not match the expected count. Then run applyAll() once.
 * The state before the run stays in File > Version history.
 */
const DOC_ID = '1FcvZa_igEO7X7qGzuZQ7sMiDCbvlj-YDIaBueJL-aSg';
const TAB_ID = 't.3l193x1g8vz7'; // document tab "Final"
const RAW = 'https://raw.githubusercontent.com/veinsan/proofskill/docs/d3-report-sync/';
const ET = DocumentApp.ElementType;

function listTabs() {
  const walk = (tabs, d) => tabs.forEach((t) => { console.log(' '.repeat(d * 2) + t.getId() + '  ' + t.getTitle()); walk(t.getChildTabs(), d + 1); });
  walk(DocumentApp.openById(DOC_ID).getTabs(), 0);
}

function body_() { return DocumentApp.openById(DOC_ID).getTab(TAB_ID).asDocumentTab().getBody(); }
function esc_(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
function blocks_(body) { const out = []; for (let i = 0; i < body.getNumChildren(); i++) { const c = body.getChild(i); if (c.getType() !== ET.TABLE_OF_CONTENTS) out.push(c); } return out; }
// The table of contents is skipped: it is rebuilt from the headings with its refresh button.
function count_(body, find) { const p = esc_(find); let n = 0; blocks_(body).forEach((c) => { let r = null; while ((r = c.findText(p, r))) n++; }); return n; }
function replaceAll_(body, find, repl) { const p = esc_(find), r = repl.replace(/\$/g, '\\$'); blocks_(body).forEach((c) => c.replaceText(p, r)); }
function clean_(a) { const o = {}; for (const k in a) if (a[k] !== null && a[k] !== undefined) o[k] = a[k]; return o; }

// ---------- text replacements: [find, replace, expected count (default 1)] ----------
// Order matters: renames that free a label (Tabel 0.3, BAB XI, 11.x) run before new content uses it.
const REPLACE = [
  // Cover and front matter
  ['TUGAS BESAR DELIVERABLE 1 & 2', 'TUGAS BESAR DELIVERABLE 1, 2 & 3'],
  ['Penutup (kini bagian Bab XI)', 'Penutup (kini Bab XII)'],
  ['Bab XI, Referensi', 'Bab XII (Penutup), Referensi'],
  ['Hasil Deliverable 2 dirangkum pada Tabel 0.3.', 'Hasil Deliverable 2 dirangkum pada Tabel 0.4. Bab XI memuat Deliverable 3, yaitu prototipe yang sudah di-deploy beserta hasil pengujiannya, yang dirangkum pada Tabel 0.5. Bab XII adalah penutup.'],
  ['Tabel 0.3', 'Tabel 0.4', 2],
  ['Belum ada wawancara dengan organisasi tertentu.', 'Validasi kebutuhan dilakukan melalui wawancara semi-terstruktur dengan empat responden (R1 sampai R4) yang mewakili penerbit, HR, dan pencari kerja (subbab 4.9).'],
  ['Prototipe dibatasi pada penerbitan, pembagian, verifikasi, pencabutan, dan satu alur pencocokan skill.', 'Prototipe dibatasi pada penerbitan, pembagian, verifikasi, pencabutan, dan satu alur pencocokan skill, dan sudah dibangun serta di-deploy di https://proofskill-two.vercel.app (Bab XI).'],
  ['Target pada tujuan layanan (Tabel 1.6) adalah target desain, angka kinerja baru dilaporkan setelah prototipe diukur pada Deliverable 3.', 'Target pada tujuan layanan (Tabel 1.6) adalah target desain. Hasil pengukuran prototipe pada Deliverable 3 dilaporkan pada subbab 11.6, dan kelima target tercapai pada data uji sintetis.'],
  ['19 operasi', '20 operasi', 2],
  ['12 endpoint di bawah /api/v1: 10 dibangun, 1 opsional, 1 hanya spesifikasi.', '14 endpoint di bawah /api/v1: 13 dibangun (API-05 yang semula opsional ikut dibangun, API-12 dan API-13 ditambahkan saat implementasi), 1 hanya spesifikasi.'],
  ['15 skenario uji awal, termasuk tiga uji pembeda blockchain.', '16 skenario uji (TC-16 ditambahkan saat implementasi), termasuk tiga uji pembeda blockchain.'],
  // Bab I and III
  ['Blockchain permissioned (konsorsium penerbit), prototipe memakai jaringan lokal', 'Blockchain dengan kontrak berizin (hanya penerbit terdaftar yang dapat mencatat), prototipe di-deploy di testnet publik Base Sepolia'],
  ['AI (embedding teks multibahasa)', 'AI (embedding dan judge model bahasa Gemini)'],
  ['prototipe akan menyimulasikannya dengan beberapa penerbit uji.', 'prototipe menyimulasikannya dengan dua penerbit uji (ISS-001 dan ISS-002).'],
  ['Registry blockchain permissioned,', 'Registry blockchain dengan kontrak berizin,'],
  ['Lebih tinggi pada jaringan dengan banyak validator, pada prototipe lokal hanya mensimulasikannya.', 'Lebih tinggi pada jaringan dengan banyak validator, prototipe memakai testnet publik Base Sepolia dengan dua penerbit uji.'],
  ['Sistem mencatat komitmen hash ber-nonce dan status di blockchain lokal.', 'Sistem mencatat komitmen hash ber-nonce dan status di blockchain (testnet Base Sepolia pada prototipe).'],
  ['Kinerja pada prototipe lokal.', 'Kinerja pada prototipe.'],
  ['mencatat penerbitan pada blockchain lokal.', 'mencatat penerbitan pada blockchain.'],
  ['pencatatan registry blockchain lokal,', 'pencatatan registry blockchain di testnet,'],
  ['Prototipe memakai jaringan lokal dengan beberapa penerbit uji, lalu membuktikan', 'Prototipe memakai testnet publik Base Sepolia dengan dua penerbit uji, lalu membuktikan'],
  // Bab IV
  [', karena wawancara dengan penyelenggara nyata belum dapat dilakukan sebelum tenggat.', ', lalu melengkapinya dengan wawancara semi-terstruktur terhadap empat responden pada Deliverable 2 (subbab 4.9).'],
  ['Belum ada temuan.', 'Penerbit masih merekap kelulusan dan menjawab pertanyaan keaslian secara manual, HR tidak dapat memastikan status pencabutan, pencari kerja ingin membatasi data yang terlihat, dan sertifikat dari banyak penyelenggara berbeda format sehingga konfirmasi harus ke tiap penerbit.'],
  ['Temuan yang diharapkan', 'Temuan utama'],
  ['Kesimpulan ini berasal dari standar, regulasi, data sekunder, dan skenario studi kasus.', 'Kesimpulan ini berasal dari standar, regulasi, data sekunder, skenario studi kasus, dan wawancara empat responden.'],
  // Bab VI
  ['Uji (TC-01–TC-15)', 'Uji (TC-01–TC-16)'],
  // Bab VIII
  ['commitment, issuerId, status, timestamp', 'commitment, issuerId, status, timestamp, issuerActive'],
  // Bab IX
  ['ID berformat kode: CRD-, ISS-, SHL-, VER-, MAT-.', 'ID berformat kode: CRD-, ISS-, SHL-, VER-, MAT-, ditambah HLD- untuk peserta dan SK- untuk skill.'],
  ['Data kredensial hanya keluar lewat token berbagi yang dibuat pemiliknya.', 'Data kredensial hanya keluar lewat token berbagi yang dibuat pemiliknya. API-12 dan API-13 hanya mendaftar kredensial milik pemanggil atau terbitan penerbit pemanggil, tanpa query atau filter.'],
  ['satu orang dapat memiliki beberapa akun untuk menyimulasikan peran berbeda.', 'satu orang dapat memiliki beberapa akun untuk menyimulasikan peran berbeda. Pada implementasi, akun disimpan di Supabase Auth: API-00 meneruskan login kata sandi ke Supabase (nama pengguna x masuk sebagai x@proofskill.example) dan mengembalikan access token JWT ES256 dari Supabase, sedangkan peran, issuerId, holderRef, dan username dibaca dari app_metadata token. Portal web tidak memiliki formulir kata sandi: login demo sekali klik dikirim ke rute server web yang menambahkan kata sandi demo lalu memanggil API-00.'],
  ['admin.unit-a', 'admin.iss001'],
  ['NIK sengaja tidak menjadi bagian payload (NFR-02).', 'NIK sengaja tidak menjadi bagian payload (NFR-02). Payload kanonik adalah JSON dengan kunci terurut tanpa spasi (UTF-8) atas credentialId, issuerId, holderRef, program.title, program.completedAt, program.criteria, dan skills (ID terurut), dan commitment = SHA-256(JSON kanonik ‖ nonce acak 32 byte). Nonce disimpan off-chain. holderRef yang tidak dikenal ditolak dengan 400 MALFORMED_REQUEST.'],
  ['URL yang dihasilkan dapat dipakai sebagai Credential URL di LinkedIn.', 'URL yang dihasilkan dapat dipakai sebagai Credential URL di LinkedIn. Field scope yang diizinkan adalah holderDisplayName, program.title, completedAt, program.criteria, dan skills, dan expiresInHours bernilai 1 sampai 720 jam.'],
  ['https://proofskill.example/v/', 'https://proofskill-two.vercel.app/v/', -1],
  ['dan data kredensial tidak dikembalikan (FR-12).', 'dan data kredensial tidak dikembalikan (FR-12). Bila beberapa pemeriksaan gagal sekaligus, result menunjuk penyebab utama dengan urutan TAMPERED, REVOKED, lalu ISSUER_UNAUTHORIZED, dan kredensial yang tidak pernah tercatat di registry dihitung TAMPERED. ISSUER_UNAUTHORIZED muncul bila getRecord melaporkan penerbit sudah dinonaktifkan (issuerActive bernilai false).'],
  ['tidak dijumlahkan menjadi skor kandidat.', 'tidak dijumlahkan menjadi skor kandidat. Deskripsi posisi (1 sampai 2.000 karakter) dipecah menjadi persyaratan pada akhir kalimat, koma, titik koma, serta kata "dan" atau "and". Setiap persyaratan dibandingkan dengan label dan alias skill terverifikasi memakai embedding gemini-embedding-001, lalu judge gemini-3.1-flash-lite memutuskan, di antara skill dengan kemiripan 0,60 atau lebih, skill mana yang mencakup persyaratan itu dan menulis alasannya. Bila judge tidak menjawab, dipakai judge cadangan gemini-3.5-flash-lite, lalu hasil judge tersimpan untuk posisi contoh, lalu embedding saja dengan ambang 0,71. Jalur yang dipakai disebut pada modelVersion.'],
  ['0.91', '0.78'],
  ['Istilah dan konteks identik', 'The skill OWASP Top 10 directly matches the requirement.'],
  ['Tidak ada skill terkait', 'No skill covers SIEM log monitoring.'],
  ['Kemiripan teks bukan bukti kemampuan.', 'Text similarity is not proof of ability.'],
  ['embedding-multibahasa-v1', 'gemini-embedding-001 (Gemini API, RETRIEVAL_QUERY/RETRIEVAL_DOCUMENT) + gemini-3.1-flash-lite judge'],
  ['Format JSON atau tipe field salah', 'Format JSON atau tipe field salah, atau holderRef tidak dikenal'],
  ['Dasar kontrol akses (NFR-01)', 'Dasar kontrol akses (NFR-01), platform_admin hanya untuk API-01'],
  // Bab X
  ['Pilihan teknologi di bawah ini adalah usulan awal yang dapat berubah saat implementasi.', 'Pilihan teknologi semula berupa usulan awal. Tabel di bab ini sudah diperbarui sesuai implementasi, dan hasil pembangunannya dilaporkan pada Bab XI.'],
  ['API-00, 01, 02, 03, 04, 06, 07, 08, 09, 10 (sepuluh endpoint) dan portal web untuk tiga peran.', 'API-00 sampai API-10 serta API-12 dan API-13 (tiga belas endpoint, termasuk API-05 yang semula opsional) dan portal web untuk tiga peran, di-deploy di https://proofskill-two.vercel.app.'],
  ['API-05 (pencabutan tautan berizin), dikerjakan bila waktu tersisa.', 'Tidak ada lagi: API-05 (pencabutan tautan berizin) sudah dibangun.'],
  ['pembayaran, blockchain publik, penyimpanan', 'pembayaran, blockchain mainnet (deployment memakai testnet publik Base Sepolia), penyimpanan'],
  ['satu katalog skill kecil, dan beberapa deskripsi posisi.', 'satu katalog skill kecil, dan beberapa deskripsi posisi. Situs publik memakai enam akun demo sintetis.'],
  ['Prototipe memakai jaringan lokal (Hardhat) dengan beberapa akun penerbit, sehingga tidak ada biaya gas nyata dan hasil dapat direproduksi penguji. Kontrak menyediakan empat fungsi: mendaftarkan penerbit, mencatat komitmen, mengubah status, dan membaca catatan, fungsi pengubah status hanya dapat dipanggil penerbit asal.',
    'Prototipe dikembangkan di jaringan lokal (Hardhat), lalu kontraknya di-deploy ke testnet publik Base Sepolia (chainId 84532) pada alamat 0xFB11769EBD22fe1Ac40391227e6526ccf077D136 dan diverifikasi di Basescan. ETH testnet tidak bernilai, sehingga tidak ada biaya gas nyata. API menandatangani setiap transaksi dengan kunci penerbit yang bertindak, disimpan sebagai secret (kustodial, OD-12), sehingga aturan penerbit asal tetap ditegakkan kontrak. Kontrak menyediakan empat fungsi: mendaftarkan penerbit, mencatat komitmen, mengubah status, dan membaca catatan, fungsi pengubah status hanya dapat dipanggil penerbit asal. Saat implementasi ditambahkan deactivateIssuer (hanya pemilik registry, tanpa endpoint) dan getter baca issuerAccountOf, dan getRecord juga mengembalikan issuerActive.'],
  ['memakai embedding teks multibahasa, lalu mengelompokkan hasil menjadi cocok dan belum tercakup.', 'memakai dua model Gemini: embedding gemini-embedding-001 menyaring skill yang mirip, lalu model bahasa gemini-3.1-flash-lite (cadangan gemini-3.5-flash-lite) memutuskan skill yang mencakup tiap persyaratan beserta alasannya, sehingga hasil terkelompok menjadi cocok dan belum tercakup.'],
  ['bukan dengan data yang dapat diubah satu pihak.', 'bukan dengan data yang dapat diubah satu pihak. Saat implementasi ditambahkan TC-16 untuk hasil keempat: kredensial dari penerbit yang dinonaktifkan pemilik registry terbaca ISSUER_UNAUTHORIZED.'],
  ['Arsitektur dan usulan stack', 'Arsitektur dan stack', -1],
  ['Usulan teknologi (belum final)', 'Teknologi yang dipakai pada prototipe'],
  ['Pilihan stack bersifat usulan. Bila tim lebih menguasai bahasa lain, pemetaan ke SoaML dan API tetap berlaku karena kontrak layanan tidak bergantung pada bahasa implementasi.',
    'Rencana awal memakai rantai Hardhat lokal dan model embedding lokal MiniLM. Saat prototipe dibawa ke deployment, registry dipindah ke testnet Base Sepolia dan AI ke Gemini API, karena model lokal membutuhkan pustaka yang tidak muat di fungsi serverless. Endpoint, payload, dan kode galat tidak berubah, karena kontrak layanan tidak bergantung pada infrastruktur.'],
  ['Jadwal awal (usulan)', 'Jadwal awal (rencana D2)'],
  // Penutup (renumbered to Bab XII before Bab XI is inserted)
  ['yang diekspos melalui 12 endpoint REST tanpa endpoint pencarian kandidat.', 'yang diekspos melalui 14 endpoint REST (13 dibangun) tanpa endpoint pencarian kandidat.'],
  ['dengan 15 skenario uji, termasuk tiga uji pembeda blockchain.', 'dengan 16 skenario uji, termasuk tiga uji pembeda blockchain.'],
  ['Tabel 11.1', 'Tabel 12.1'],
  ['Deliverable 3 mengimplementasikan prototipe sesuai Bab X, menjalankan skenario TC-01 sampai TC-15, dan melaporkan hasilnya terhadap tujuan T-01 sampai T-05, lengkap dengan langkah, masukan, hasil yang diharapkan, hasil aktual, status, dan bukti uji.',
    'Deliverable 3 sudah mengimplementasikan prototipe sesuai Bab X, menjalankan skenario TC-01 sampai TC-16 dengan hasil 16 lulus, dan melaporkan hasilnya terhadap tujuan T-01 sampai T-05 lengkap dengan langkah, masukan, hasil yang diharapkan, hasil aktual, status, dan bukti uji (Bab XI). Langkah berikutnya adalah rencana pengembangan pada subbab 11.8.'],
  ['TC-01 sampai TC-15', 'TC-01 sampai TC-16', -1],
];

// ---------- element helpers ----------
function findPara_(body, re, from) {
  for (let i = from || 0; i < body.getNumChildren(); i++) {
    const c = body.getChild(i), ty = c.getType();
    if ((ty === ET.PARAGRAPH || ty === ET.LIST_ITEM) && re.test(c.asText().getText().trim())) return c;
  }
  return null;
}
function mustPara_(body, re) { const p = findPara_(body, re); if (!p) throw new Error('Paragraph not found: ' + re); return p; }
function tableAfter_(body, caption) {
  const p = mustPara_(body, new RegExp('^' + esc_(caption) + '(?![0-9])'));
  const start = body.getChildIndex(p);
  for (let i = start + 1; i < Math.min(start + 5, body.getNumChildren()); i++) {
    if (body.getChild(i).getType() === ET.TABLE) return body.getChild(i).asTable();
  }
  throw new Error('Table not found after ' + caption);
}
function rowOf_(table, first) {
  for (let r = 0; r < table.getNumRows(); r++) if (table.getCell(r, 0).getText().trim().indexOf(first) === 0) return r;
  throw new Error('Row "' + first + '" not found');
}
function setCell_(cell, text, bold) {
  const p0 = cell.getChild(0).asParagraph();
  const pa = clean_(p0.getAttributes());
  const t0 = p0.editAsText();
  const ta = t0.getText().length ? clean_(t0.getAttributes(0)) : {};
  delete ta[DocumentApp.Attribute.LINK_URL];
  cell.setText(text);
  const p = cell.getChild(0).asParagraph();
  p.setAttributes(pa);
  if (text.length) {
    const t = p.editAsText();
    t.setAttributes(0, text.length - 1, ta);
    t.setBold(bold === undefined ? !!ta[DocumentApp.Attribute.BOLD] : bold);
  }
}
function setRow_(table, r, values) { values.forEach((v, j) => { if (v !== null) setCell_(table.getCell(r, j), v); }); }
function insertRowAfter_(table, r, values) {
  const row = table.insertTableRow(r + 1, table.getRow(r).copy());
  values.forEach((v, j) => setCell_(row.getCell(j), v, false));
  return row;
}
function buildTable_(tmpl, rows) {
  const t = tmpl.copy();
  while (t.getNumRows() > rows.length) t.removeRow(t.getNumRows() - 1);
  while (t.getNumRows() < rows.length) t.appendTableRow(t.getRow(t.getNumRows() - 1).copy());
  rows.forEach((r, i) => r.forEach((v, j) => setCell_(t.getCell(i, j), v, i === 0)));
  return t;
}
function para_(tmpl, text, boldPrefix) {
  const p = tmpl.copy();
  const t = p.editAsText();
  const a = t.getText().length ? clean_(t.getAttributes(0)) : {};
  delete a[DocumentApp.Attribute.LINK_URL];
  t.setText(text);
  if (text.length) {
    t.setAttributes(0, text.length - 1, a);
    t.setBold(false); t.setItalic(false);
    if (boldPrefix) t.setBold(0, boldPrefix.length - 1, true);
  }
  return p;
}
function heading_(tmpl, from, to) { const h = tmpl.copy(); h.editAsText().replaceText(esc_(from), to); return h; }
function caption_(tmpl, label, rest) { return para_(tmpl, label + ' ' + rest, label); }

/** Inserts elements one after another starting at a body index. */
function Ins_(body, index) { this.b = body; this.i = index; }
Ins_.prototype.add = function (el) {
  const ty = el.getType();
  let r;
  if (ty === ET.TABLE) r = this.b.insertTable(this.i, el);
  else if (ty === ET.LIST_ITEM) r = this.b.insertListItem(this.i, el);
  else r = this.b.insertParagraph(this.i, el);
  this.i++;
  return r;
};
Ins_.prototype.image = function (path, widthPt, fallbackTmpl) {
  const p = this.b.insertParagraph(this.i++, '');
  p.setAlignment(DocumentApp.HorizontalAlignment.CENTER);
  try {
    const blob = UrlFetchApp.fetch(RAW + path).getBlob();
    const img = p.appendInlineImage(blob);
    const w = img.getWidth(), h = img.getHeight();
    img.setWidth(widthPt).setHeight(Math.round(h * widthPt / w));
  } catch (e) {
    p.appendText('[Gambar belum termuat: ' + path + ']');
    console.log('IMAGE FAILED ' + path + ': ' + e);
  }
  return p;
};

// ---------- entry points ----------
function dryRun() {
  const body = body_();
  let bad = 0;
  // Counts are taken on the unchanged document, so finds that only exist after an earlier
  // replacement (the Penutup lines that mention 20 operasi) report 0 here; they are marked "after".
  REPLACE.forEach(([f, , n]) => {
    const want = n === undefined ? 1 : n;
    const got = count_(body, f);
    const ok = want === -1 ? got >= 1 : got === want;
    if (!ok) { bad++; console.log('MISMATCH want ' + want + ' got ' + got + ': ' + f.slice(0, 90)); }
  });
  ['Tabel 0.2', 'Tabel 0.3', 'Tabel 4.1', 'Tabel 4.17', 'Tabel 8.4', 'Tabel 9.1', 'Tabel 9.2', 'Tabel 9.15', 'Tabel 9.16', 'Tabel 9.17', 'Tabel 10.1', 'Tabel 10.2', 'Tabel 10.3', 'Tabel 10.4']
    .forEach((c) => { try { const t = tableAfter_(body, c); console.log(c + ': ' + t.getNumRows() + ' x ' + t.getRow(0).getNumCells()); } catch (e) { bad++; console.log('NO TABLE ' + c); } });
  [/^BAB X\b/, /^BAB XI\b/, /^10\.1 Lingkup prototipe/, /^Bab ini menyiapkan Deliverable 3/, /^Gambar 10\.1/, /^Proses As-Is terpetakan/, /^Ringkasan Eksekutif$/, /^Daftar Isi$/, /^REFERENSI$/, /^BCA Sekuritas/, /^Good News from Indonesia/, /^Suhardi dkk/, /^W3C\. \(2025\)/, /^Kelayakan dijaga/, /^11\.3 Rencana Deliverable 3/, /^11\.1 Kesimpulan/, /^11\.2 Keterkaitan/]
    .forEach((re) => { const p = findPara_(body, re); console.log((p ? 'ok   ' : 'MISSING ') + re + (p ? '  ' + JSON.stringify(p.getText().slice(0, 50)) : '')); if (!p) bad++; });
  try { UrlFetchApp.fetch(RAW + 'docs/figures/arsitektur-deployed.png'); console.log('image URL ok'); } catch (e) { bad++; console.log('IMAGE URL FAILED: ' + e); }
  console.log(bad ? bad + ' problem(s)' : 'dry run clean');
}

function applyAll() {
  const body = body_(); // the previous state stays in File > Version history

  // Templates are copied before anything changes.
  const T = {
    h1: mustPara_(body, /^BAB X\b/).copy(),
    h1front: mustPara_(body, /^Ringkasan Eksekutif$/).copy(),
    h2: mustPara_(body, /^10\.1 Lingkup prototipe/).copy(),
    p: mustPara_(body, /^Bab ini menyiapkan Deliverable 3/).copy(),
    cap: mustPara_(body, /^Tabel 10\.4(?![0-9])/).copy(),
    li: mustPara_(body, /^Proses As-Is terpetakan/).copy(),
    ref: mustPara_(body, /^Nomic Foundation/).copy(),
    t2: tableAfter_(body, 'Tabel 0.3').copy(), // 2 columns (D2 summary)
    t3: tableAfter_(body, 'Tabel 9.16').copy(),
    t4: tableAfter_(body, 'Tabel 10.4').copy(),
    t4b: tableAfter_(body, 'Tabel 0.2').copy(),
    t5: tableAfter_(body, 'Tabel 4.17').copy(),
    t6: tableAfter_(body, 'Tabel 9.2').copy(),
    t7: tableAfter_(body, 'Tabel 10.2').copy(),
  };

  // 1. Text replacements.
  REPLACE.forEach(([f, r]) => replaceAll_(body, f, r));

  // 2. Penutup becomes Bab XII.
  const penutup = mustPara_(body, /^BAB XI\b/);
  penutup.editAsText().replaceText('BAB XI', 'BAB XII');
  mustPara_(body, /^11\.1 Kesimpulan/).editAsText().replaceText('11\\.1', '12.1');
  mustPara_(body, /^11\.2 Keterkaitan/).editAsText().replaceText('11\\.2', '12.2');
  const h123 = mustPara_(body, /^11\.3 Rencana Deliverable 3/);
  h123.editAsText().setText('12.3 Status Deliverable 3 dan langkah berikutnya');

  // 3. Table edits.
  tableEdits_(body);

  // 4. Gambar 10.1 is replaced by the deployed architecture.
  replaceFigure_(body, /^Gambar 10\.1/, 'docs/figures/arsitektur-deployed.png', 450);

  // 5. New sections.
  frontMatter_(body, T);
  codesNote_(body, T);
  chapterD3_(body, T);
  conclusion_(body, T);
  appendix_(body, T);
  references_(body, T);
  console.log('done; refresh the table of contents (click it, then the refresh icon)');
}

function tableEdits_(body) {
  // Tabel 4.1: interview row is now done.
  const t41 = tableAfter_(body, 'Tabel 4.1');
  const r41 = rowOf_(t41, 'Wawancara');
  t41.getCell(r41, 3).editAsText().replaceText('Rencana', 'Fakta');
  t41.getCell(r41, 3).editAsText().replaceText('belum dilaksanakan', 'dilakukan');

  // Tabel 8.4: listOwnCredentials (API-12, API-13).
  const t84 = tableAfter_(body, 'Tabel 8.4');
  let r = -1;
  for (let i = 0; i < t84.getNumRows(); i++) if (t84.getCell(i, 1).getText().trim() === 'getCredential') r = i;
  insertRowAfter_(t84, r, ['CIS', 'listOwnCredentials', 'Token holder atau issuer_admin, limit, offset', '{items, total}', 'FR-05', 'Masuk ke T07 dan T24', 'API-12, API-13']);

  // Tabel 9.1: authentication.
  const t91 = tableAfter_(body, 'Tabel 9.1');
  setCell_(t91.getCell(rowOf_(t91, 'Autentikasi'), 1), 'Authorization: Bearer <accessToken> dari API-00. Token adalah JWT ES256 yang diterbitkan Supabase Auth, dan app_metadata-nya memuat peran (issuer_admin, holder, verifier, atau platform_admin khusus API-01), issuerId, holderRef, dan username. Akun verifier gratis.', false);

  // Tabel 9.2: API-05 built, API-12 and API-13 added.
  const t92 = tableAfter_(body, 'Tabel 9.2');
  setCell_(t92.getCell(rowOf_(t92, 'API-05'), 5), 'Prototipe (opsional, dibangun)', false);
  const r11 = rowOf_(t92, 'API-11');
  insertRowAfter_(t92, r11, ['API-12', 'GET /holders/me/credentials', 'Mendaftar kredensial milik peserta', 'holder', 'CIS.listOwnCredentials', 'Prototipe (ditambahkan)']);
  insertRowAfter_(t92, r11 + 1, ['API-13', 'GET /issuers/me/credentials', 'Mendaftar kredensial terbitan penerbit', 'issuer_admin', 'CIS.listOwnCredentials', 'Prototipe (ditambahkan)']);

  // Tabel 9.15: named fields and codes, plus API-12 and API-13.
  const t915 = tableAfter_(body, 'Tabel 9.15');
  setRow_(t915, rowOf_(t915, 'API-01'), [null, '{name, unitType, registryAccount} dengan token platform_admin', '201 IssuerRecord {issuerId, name, unitType, registryAccount, txHash, registeredAt}, 403 FORBIDDEN_ROLE bila bukan platform_admin, 409 ISSUER_ALREADY_REGISTERED bila sudah terdaftar', null]);
  setRow_(t915, rowOf_(t915, 'API-03'), [null, null, '200 CredentialView {credentialId, issuer, holderRef, holderDisplayName, program, skills, status, commitment, txHash, issuedAt, revokedAt, revocationReason, shareLinks}, 403 NOT_CREDENTIAL_OWNER bila bukan pemilik atau penerbit asal, 404 CREDENTIAL_NOT_FOUND', null]);
  setRow_(t915, rowOf_(t915, 'API-05'), [null, null, '204 tanpa isi, 403 NOT_CREDENTIAL_OWNER bila bukan pemilik, 404 SHARE_LINK_NOT_FOUND bila tidak ada', 'Dibangun (tombol Revoke di portal peserta), memperkuat kendali peserta (O-06)']);
  const r10 = rowOf_(t915, 'API-10');
  setRow_(t915, r10, [null, 'Header token issuer_admin, filter operation, from, to, limit (bawaan 50, maksimum 200), offset', null, 'Tanpa isi payload sensitif (NFR-07), tiap penerbit hanya melihat peristiwa kredensialnya sendiri']);
  insertRowAfter_(t915, r10, ['API-12 GET /holders/me/credentials', 'Header token holder, limit dan offset', '200 {items: [{credentialId, issuer, holderRef, holderDisplayName, program, status, issuedAt, revokedAt}], total}, 403 FORBIDDEN_ROLE bila bukan holder', 'Ditambahkan saat implementasi, hanya kredensial milik pemanggil, tanpa query atau filter']);
  insertRowAfter_(t915, r10 + 1, ['API-13 GET /issuers/me/credentials', 'Header token issuer_admin, limit dan offset', 'Bentuk sama dengan API-12, 403 FORBIDDEN_ROLE bila bukan issuer_admin, 403 ISSUER_NOT_AUTHORIZED bila akun tidak terikat penerbit', 'Ditambahkan saat implementasi, hanya kredensial terbitan penerbit pemanggil']);

  // Tabel 9.16: roles.
  const t916 = tableAfter_(body, 'Tabel 9.16');
  setCell_(t916.getCell(rowOf_(t916, 'Peran'), 1), 'issuer_admin, holder, verifier, platform_admin', false);

  // Tabel 9.17: portal lists lead into T07 and T24.
  const t917 = tableAfter_(body, 'Tabel 9.17');
  setRow_(t917, rowOf_(t917, 'T07'), [null, null, null, 'CIS.listOwnCredentials, CIS.getCredential', 'API-12, API-03', null]);
  setRow_(t917, rowOf_(t917, 'T24'), [null, null, null, 'CIS.listOwnCredentials, CSS.revokeCredential', 'API-13, API-09', null]);

  // Tabel 10.2: endpoints per feature.
  const t102 = tableAfter_(body, 'Tabel 10.2');
  setCell_(t102.getCell(rowOf_(t102, 'F-03'), 4), 'API-03, 04, 05, 12', false);
  setCell_(t102.getCell(rowOf_(t102, 'F-05'), 4), 'API-09, 13', false);

  // Tabel 10.3: the stack that was built.
  const t103 = tableAfter_(body, 'Tabel 10.3');
  setCell_(t103.getCell(0, 1), 'Teknologi', true);
  setRow_(t103, rowOf_(t103, 'Antarmuka web'), [null, 'Next.js 16 (React 19, TypeScript) di Vercel', 'Tiga portal pada satu aplikasi, mem-proxy /api/v1 ke API sehingga API tidak perlu CORS.']);
  setRow_(t103, rowOf_(t103, 'Layanan API'), [null, 'FastAPI 0.165 (Python 3.13) sebagai fungsi Python di Vercel, region sin1', 'Satu modul per layanan SoaML, skema OpenAPI otomatis dari kontrak.']);
  setRow_(t103, rowOf_(t103, 'Basis data off-chain'), [null, 'Supabase Postgres (Singapura), PostgreSQL 17 lokal untuk pengembangan', 'Metadata kredensial, tautan, katalog, verifikasi, dan audit. Row Level Security aktif tanpa policy, hanya koneksi API yang dapat membaca.']);
  const rReg = rowOf_(t103, 'Registry');
  setRow_(t103, rReg, [null, 'Kontrak Solidity ProofSkillRegistry di testnet Base Sepolia, Hardhat untuk uji kontrak dan rantai lokal', 'Mendaftarkan penerbit, mencatat komitmen, mengubah status, membaca catatan, menonaktifkan penerbit. Terverifikasi di Basescan.']);
  setRow_(t103, rowOf_(t103, 'AI'), [null, 'Gemini API: gemini-embedding-001, judge gemini-3.1-flash-lite, cadangan gemini-3.5-flash-lite', 'Dipilih lewat gold set terkunci (F1 uji 94,4%). Model lokal membutuhkan pustaka yang tidak muat di fungsi serverless.']);
  insertRowAfter_(t103, rReg, ['Autentikasi', 'Supabase Auth (JWT ES256) di balik API-00', 'Peran dan identitas penerbit atau peserta dibaca dari app_metadata yang hanya dapat ditulis kunci service role.']);

  // Tabel 10.4: TC-16.
  const t104 = tableAfter_(body, 'Tabel 10.4');
  insertRowAfter_(t104, rowOf_(t104, 'TC-15'), ['TC-16', 'Admin platform menonaktifkan penerbit di registry, lalu kredensialnya diverifikasi', '200, result ISSUER_UNAUTHORIZED, issuerAuthorized FAIL', 'API-06, FR-06, ditambahkan saat implementasi']);

  // Tabel 12.1 (was 11.1): TC-16 joins verification.
  const t121 = tableAfter_(body, 'Tabel 12.1');
  for (let i = 1; i < t121.getNumRows(); i++) {
    const c = t121.getCell(i, 7);
    if (c.getText().trim() === 'TC-04, 05, 12') setCell_(c, 'TC-04, 05, 12, 16', false);
  }
}

function replaceFigure_(body, captionRe, path, widthPt) {
  const cap = mustPara_(body, captionRe);
  const idx = body.getChildIndex(cap);
  for (const j of [idx - 1, idx + 1, idx - 2]) {
    const el = body.getChild(j);
    if (el.getType() !== ET.PARAGRAPH) continue;
    const p = el.asParagraph();
    for (let k = 0; k < p.getNumChildren(); k++) {
      if (p.getChild(k).getType() === ET.INLINE_IMAGE) {
        const old = p.getChild(k).asInlineImage();
        const blob = UrlFetchApp.fetch(RAW + path).getBlob();
        const img = p.insertInlineImage(k, blob);
        img.setWidth(widthPt).setHeight(Math.round(img.getHeight() * widthPt / img.getWidth()));
        old.removeFromParent();
        cap.editAsText().replaceText('Arsitektur prototipe$', 'Arsitektur prototipe yang di-deploy');
        return;
      }
    }
  }
  console.log('Figure image not found next to ' + captionRe + ' (it may be a drawing); replace it by hand with ' + RAW + path);
}

function frontMatter_(body, T) {
  // Tabel 0.3: Deliverable 3 task table, right after Tabel 0.2.
  const t02 = tableAfter_(body, 'Tabel 0.2');
  let ins = new Ins_(body, body.getChildIndex(t02) + 1);
  ins.add(caption_(T.cap, 'Tabel 0.3', 'Pembagian tugas dan kontribusi anggota Deliverable 3'));
  ins.add(buildTable_(T.t4b, [
    ['Anggota', 'NIM', 'Bagian yang dikerjakan', 'Kontribusi'],
    ['M. Faris Daffa', '18224025', '[isi]', '[isi]'],
    ['Nafhan Shafy Aulia', '18224027', '[isi]', '[isi]'],
    ['Irghi Satya P.', '18224041', '[isi]', '[isi]'],
    ['Mishael Gilland', '18224005', 'Redesign antarmuka web (liquid glass, halaman awal, halaman login, aset 3D, menu akun) [lengkapi]', '[isi]'],
    ['Bryant Azraqi', '18224067', '[isi]', '[isi]'],
    ['Riantama Putra', '18224061', 'Implementasi dan deployment prototipe (kontrak registry, REST API, portal web, Supabase, Base Sepolia, Gemini), pengujian TC-01 sampai TC-16, evaluasi AI, penyesuaian laporan dan deck [lengkapi]', '[isi]'],
    ['Total', '', '', '100%'],
  ]));

  // Tabel 0.5: Deliverable 3 summary, right after Tabel 0.4 (the former 0.3).
  const t04 = tableAfter_(body, 'Tabel 0.4');
  ins = new Ins_(body, body.getChildIndex(t04) + 1);
  ins.add(caption_(T.cap, 'Tabel 0.5', 'Ringkasan hasil Deliverable 3'));
  ins.add(buildTable_(T.t2, [
    ['Hasil', 'Isi'],
    ['Prototipe', 'Web tiga portal (Next.js), REST API FastAPI dengan 13 endpoint, Supabase Postgres dan Auth, registry di testnet Base Sepolia, dan pencocokan skill dengan model Gemini. Publik di https://proofskill-two.vercel.app.'],
    ['Pengujian', '16 dari 16 skenario lulus pada stack deployed dan pada stack lokal. 193 tes API (pytest) dan 15 tes kontrak (Hardhat) lulus.'],
    ['Tujuan layanan', 'T-01 median 0,441 detik per verifikasi, T-02 nol langkah admin, T-03 tanpa data pribadi on-chain, T-04 3 dari 3 ringkasan berlabel REKOMENDASI, T-05 5 dari 5 verifikasi tetap REVOKED.'],
    ['Evaluasi AI', 'Judge gemini-3.1-flash-lite mencapai F1 94,4% (precision 100%) pada 39 butir uji gold set, naik dari 82,9% untuk embedding saja, dan benar pada 5 dari 5 persyaratan bernegasi.'],
    ['Keterbatasan', 'Data sintetis, free tier Gemini, kunci penerbit kustodial, dan login demo publik (subbab 11.7).'],
  ]));

  // Catatan Revisi, restored before Daftar Isi.
  const daftar = mustPara_(body, /^Daftar Isi$/);
  ins = new Ins_(body, body.getChildIndex(daftar));
  ins.add(heading_(T.h1front, 'Ringkasan Eksekutif', 'Catatan Revisi'));
  ins.add(para_(T.p, 'Tabel 0.6 mencatat masukan atas Deliverable 1 dan perubahannya, serta penyesuaian laporan dengan prototipe pada Deliverable 3.'));
  ins.add(caption_(T.cap, 'Tabel 0.6', 'Catatan revisi'));
  ins.add(buildTable_(T.t4, [
    ['No', 'Masukan atau temuan', 'Perubahan', 'Lokasi'],
    ['1', 'Produk belum jelas: pencari talenta, penyimpan sertifikat, atau sekadar verifikasi?', 'Definisi produk satu kalimat, jawaban atas tiga kemungkinan bentuk produk, pelanggan utama, dan aturan desain', 'Ringkasan Eksekutif, 1.3'],
    ['2', 'Apa bedanya dengan LinkedIn?', 'Pembanding dengan LinkedIn, platform e-sertifikat, dan jalur formal, tiga pembeda ProofSkill', '1.3'],
    ['3', 'Tujuan layanan hanya dua kalimat dan belum terukur', 'Tujuan T-01 sampai T-05 dengan indikator dan target desain', '1.4'],
    ['4', 'Alasan blockchain memuat kriteria “kesesuaian ketentuan tugas”', 'Diganti alasan registry bersama lintas penerbit tanpa operator tunggal', '1.3, 1.4, 4.6'],
    ['5', 'BMC To-Be memotret penyelenggara, mencantumkannya juga sebagai segmen, dan bertumpu pada verifikasi berbayar', 'BMC To-Be memotret ProofSkill sebagai layanan, penerbit pelanggan utama, verifikasi gratis', 'Bab III'],
    ['6', 'Service Blueprint tanpa panah interaksi, aksi pemeriksa di onstage, distribusi dan pencabutan tidak eksplisit', 'Blueprint As-Is dan To-Be digambar ulang: enam tahap, aksi peserta dan pemeriksa dipisah, panah antarlapisan', 'Bab V'],
    ['7', 'AI belum terpetakan ke aktivitas value chain', 'Pemanfaatan dengan AI dipetakan sebagai perluasan SE-01', '2.2'],
    ['8', 'Gambar dan tabel tanpa nomor, total kontribusi 102%', 'Caption pada semua gambar dan tabel, kontribusi dibagi rata menjadi 100%', 'Seluruh laporan'],
    ['9', 'Desain teknis perlu sama dengan prototipe yang dibangun (Deliverable 3)', 'API-12 dan API-13, TC-16, peran platform_admin, kode ISSUER_ALREADY_REGISTERED, stack deployment, dan model Gemini dimasukkan, kode galat yang belum bernama diberi nama', 'Bab I, VIII, IX, X, XI'],
  ]));
}

function codesNote_(body, T) {
  const t916 = tableAfter_(body, 'Tabel 9.16');
  const ins = new Ins_(body, body.getChildIndex(t916) + 1);
  ins.add(para_(T.p, 'Kode galat mengikuti tabel per endpoint pada subbab 9.3 dan 9.4. Saat implementasi, kode yang semula belum bernama diberi nama: API-01 memakai FORBIDDEN_ROLE (403) dan satu kode baru, ISSUER_ALREADY_REGISTERED (409), API-03 memakai NOT_CREDENTIAL_OWNER (403) dan CREDENTIAL_NOT_FOUND (404), dan API-05 memakai NOT_CREDENTIAL_OWNER (403) dan SHARE_LINK_NOT_FOUND (404). MALFORMED_REQUEST (400), UNAUTHENTICATED (401), dan REGISTRY_UNAVAILABLE (503) juga berlaku pada endpoint lain yang menerima body JSON, membutuhkan token, atau memanggil registry. Tidak ada kode lain yang ditambahkan.'));
}

function chapterD3_(body, T) {
  const penutup = mustPara_(body, /^BAB XII\b/);
  const ins = new Ins_(body, body.getChildIndex(penutup));
  const P = (t, b) => ins.add(para_(T.p, t, b));
  const H2 = (t) => ins.add(heading_(T.h2, '10.1 Lingkup prototipe', t));
  const CAP = (l, r) => ins.add(caption_(T.cap, l, r));
  const LI = (t) => ins.add(para_(T.li, t));
  const FIG = (path, w, label, rest) => { ins.image(path, w); CAP(label, rest); };

  ins.add(heading_(heading_(T.h1, 'BAB X', 'BAB XI'), 'Rencana Implementasi Prototipe', 'Prototipe dan Pengujian'));
  P('Bab ini memuat Deliverable 3. Prototipe ProofSkill dibangun dari rancangan Bab VII sampai X, lalu di-deploy sebagai layanan yang dapat dibuka publik. Kontrak API, kode galat, dan enumerasi tetap sama dengan Bab IX. Hal yang muncul saat implementasi, yaitu API-12, API-13, TC-16, peran platform_admin, dan kode ISSUER_ALREADY_REGISTERED, sudah dimasukkan ke bab terkait. Seluruh data bersifat sintetis (asumsi A6).');

  H2('11.1 Prototipe yang dibangun');
  P('Prototipe terdiri atas aplikasi web tiga portal, REST API, basis data off-chain, kontrak registry di testnet publik, dan modul AI. Tabel 11.1 merangkum komponen beserta lokasinya, dan Gambar 10.1 menunjukkan hubungan antarkomponen.');
  CAP('Tabel 11.1', 'Komponen prototipe dan lokasi deployment');
  ins.add(buildTable_(T.t3, [
    ['Komponen', 'Teknologi', 'Lokasi'],
    ['Aplikasi web', 'Next.js 16, React 19, TypeScript, three.js untuk sertifikat 3D, Lenis untuk gulir halus', 'https://proofskill-two.vercel.app (Vercel)'],
    ['REST API', 'FastAPI 0.165 di Python 3.13, satu modul per layanan SoaML', 'https://proofskill-api.vercel.app/api/v1, dokumentasi di /api/v1/docs (Vercel, sin1)'],
    ['Basis data off-chain', 'Supabase Postgres, Row Level Security aktif tanpa policy', 'Supabase, Singapura'],
    ['Autentikasi', 'Supabase Auth, JWT ES256 diverifikasi lewat JWKS', 'Supabase, dipanggil lewat API-00'],
    ['Registry blockchain', 'Kontrak Solidity ProofSkillRegistry (Hardhat 3, Solidity 0.8.28)', 'Base Sepolia, 0xFB11769EBD22fe1Ac40391227e6526ccf077D136, terverifikasi di Basescan'],
    ['Modul AI', 'gemini-embedding-001, judge gemini-3.1-flash-lite, cadangan gemini-3.5-flash-lite', 'Gemini API (free tier), dipanggil hanya oleh AMS'],
    ['Kode dan bukti uji', 'Monorepo contracts/, api/, web/, docs/evidence/', 'https://github.com/veinsan/proofskill'],
  ]));
  P('Endpoint yang dibangun berjumlah tiga belas: API-00 sampai API-10 serta API-12 dan API-13. API-05 yang semula opsional ikut dibangun, sedangkan API-11 tetap hanya spesifikasi karena FR-11 ditunda. API-12 dan API-13 ditambahkan karena portal membutuhkan daftar kredensial milik peserta dan kredensial terbitan penerbit, padahal Bab IX tidak memiliki endpoint daftar. Keduanya hanya mengembalikan data milik pemanggil tanpa query atau filter, sehingga aturan tanpa pencarian kandidat tetap terjaga.');
  P('Situs publik menyediakan login demo sekali klik untuk enam akun sintetis (Tabel 11.2). Peramban hanya mengirim nama pengguna, lalu server web menambahkan kata sandi demo yang disimpan sebagai variabel lingkungan dan memanggil API-00. Akun platform.admin hanya dapat dipakai lewat API.');
  CAP('Tabel 11.2', 'Akun demo pada situs publik');
  ins.add(buildTable_(T.t3, [
    ['Akun', 'Peran', 'Keterangan'],
    ['admin.iss001', 'issuer_admin', 'Admin Unit Pelatihan Contoh (ISS-001)'],
    ['admin.iss002', 'issuer_admin', 'Admin Himpunan Mahasiswa Contoh (ISS-002), penerbitnya dinonaktifkan permanen di registry oleh TC-16'],
    ['holder.a', 'holder', 'Peserta HLD-2026-0007'],
    ['holder.b', 'holder', 'Peserta HLD-2026-0008'],
    ['verifier.a', 'verifier', 'Recruiter, PT Contoh Digital'],
    ['verifier.b', 'verifier', 'Selection committee, Beasiswa Contoh'],
  ]));

  H2('11.2 Demonstrasi alur layanan utama');
  P('Alur utama didemonstrasikan dari browser pada situs deployed dan mengikuti lima subproses BPMN To-Be. Pengguna membuka halaman awal, memilih peran, lalu masuk dengan satu klik (Gambar 11.1 dan Gambar 11.2).');
  FIG('docs/evidence/ui/landing.jpg', 440, 'Gambar 11.1', 'Halaman awal ProofSkill');
  FIG('docs/evidence/ui/signin.jpg', 440, 'Gambar 11.2', 'Login demo dengan pilihan peran');
  P('Penerbitan (T01 sampai T06). Admin ISS-001 memilih skill dari katalog (API-08) dan menerbitkan kredensial (API-02). API menghitung komitmen SHA-256 ber-nonce, mencatatnya ke Base Sepolia, menyimpan txHash, dan menampilkan pass kredensial dengan status ACTIVE beserta panel pencabutan (Gambar 11.3 dan Gambar 11.4).', 'Penerbitan (T01 sampai T06).');
  FIG('docs/evidence/ui/issuer-issue-form.jpg', 400, 'Gambar 11.3', 'Formulir penerbitan dengan katalog skill');
  FIG('docs/evidence/ui/issuer-credential.jpg', 400, 'Gambar 11.4', 'Pass kredensial di portal penerbit beserta panel pencabutan');
  P('Distribusi (T07 sampai T10). Peserta melihat kredensial miliknya (API-12 dan API-03), mencentang field yang boleh dilihat, memilih masa berlaku, lalu membuat tautan berizin beserta kode QR (API-04). Tautan yang tidak diperlukan dapat dicabut (API-05) (Gambar 11.5).', 'Distribusi (T07 sampai T10).');
  FIG('docs/evidence/ui/holder-share-link.jpg', 400, 'Gambar 11.5', 'Pengaturan scope dan masa berlaku tautan di portal peserta');
  P('Verifikasi (T11 sampai T17). Pemeriksa membuka tautan, dan halaman /v/{shareToken} langsung menjalankan API-06. Hasil VALID menampilkan tiga pemeriksaan (integritas, penerbit, status), field dalam scope, dan referensi transaksi (Gambar 11.6).', 'Verifikasi (T11 sampai T17).');
  FIG('docs/evidence/ui/verifier-valid.jpg', 400, 'Gambar 11.6', 'Hasil verifikasi VALID');
  P('Pemanfaatan dengan AI (T18 sampai T23). Untuk hasil VALID, pemeriksa mengisi judul dan deskripsi posisi lalu menekan Check skill fit (API-07). Keluaran memuat pasangan skill dan persyaratan yang cocok beserta alasan dari judge, persyaratan yang belum tercakup, batasan model, label REKOMENDASI, dan modelVersion, tanpa skor total (Gambar 11.7).', 'Pemanfaatan dengan AI (T18 sampai T23).');
  FIG('docs/evidence/ui/verifier-skill-fit.jpg', 400, 'Gambar 11.7', 'Ringkasan kecocokan skill berlabel REKOMENDASI');
  P('Pencabutan (T24 sampai T28) dan hasil tidak sah. Penerbit asal mencabut kredensial dengan alasan (API-09), dan verifikasi berikutnya terbaca REVOKED beserta alasannya. Kredensial yang diubah di basis data terbaca TAMPERED tanpa menampilkan isinya, dan kredensial dari penerbit yang dinonaktifkan terbaca ISSUER_UNAUTHORIZED. Pada ketiga hasil ini ringkasan skill tidak ditawarkan (Gambar 11.8 sampai Gambar 11.10). Semua operasi tercatat pada log audit tanpa payload sensitif (Gambar 11.11).', 'Pencabutan (T24 sampai T28) dan hasil tidak sah.');
  FIG('docs/evidence/ui/verifier-revoked.jpg', 400, 'Gambar 11.8', 'Hasil verifikasi REVOKED beserta alasan dari penerbit');
  FIG('docs/evidence/ui/verifier-tampered.jpg', 400, 'Gambar 11.9', 'Hasil verifikasi TAMPERED dengan data disembunyikan');
  FIG('docs/evidence/ui/verifier-issuer-unauthorized.jpg', 400, 'Gambar 11.10', 'Hasil verifikasi ISSUER_UNAUTHORIZED');
  FIG('docs/evidence/ui/issuer-audit.jpg', 400, 'Gambar 11.11', 'Log audit di portal penerbit');

  H2('11.3 Interaksi layanan dan API');
  P('Tabel 11.3 memetakan setiap langkah demonstrasi ke endpoint, operasi SoaML, aktivitas BPMN To-Be, dan teknologi yang berperan.');
  CAP('Tabel 11.3', 'Langkah demonstrasi, endpoint, operasi SoaML, dan BPMN');
  ins.add(buildTable_(T.t6, [
    ['Langkah', 'Portal', 'Endpoint', 'Operasi SoaML', 'BPMN', 'BC/AI'],
    ['Login demo', 'Semua', 'API-00', 'IAS.issueAccessToken', 'Prasyarat', '-'],
    ['Pilih skill dari katalog', 'Penerbit', 'API-08', 'SCS.listSkills', 'T01', '-'],
    ['Terbitkan kredensial', 'Penerbit', 'API-02', 'CIS.issueCredential, RGS.anchorCommitment', 'T02 sampai T06', 'BC'],
    ['Lihat kredensial milik sendiri', 'Peserta', 'API-12, API-03', 'CIS.listOwnCredentials, CIS.getCredential', 'T07', '-'],
    ['Buat atau cabut tautan berizin', 'Peserta', 'API-04, API-05', 'AAS.createShareLink, AAS.revokeShareLink', 'T08 sampai T10', '-'],
    ['Buka tautan dan verifikasi', 'Pemeriksa', 'API-06', 'VRS.verifyCredential, RGS.getRecord', 'T11 sampai T17', 'BC'],
    ['Ringkasan kecocokan skill', 'Pemeriksa', 'API-07', 'AMS.matchSkills', 'T18 sampai T22', 'AI'],
    ['Daftar kredensial terbitan dan cabut', 'Penerbit', 'API-13, API-09', 'CIS.listOwnCredentials, CSS.revokeCredential, RGS.setStatus', 'T24 sampai T27', 'BC'],
    ['Baca log audit', 'Penerbit', 'API-10', 'AAS.queryAuditLog', 'Pemantauan', '-'],
  ]));
  P('Tabel 11.4 adalah respons nyata API-07 dari situs deployed pada 21 November 2026 untuk kredensial CRD-0006 dan posisi contoh Junior Security Analyst. Respons tiba dalam 3,5 detik, berlabel REKOMENDASI, memuat empat batasan, dan modelVersion-nya menyebut kedua model (gemini-embedding-001 dan judge gemini-3.1-flash-lite).');
  CAP('Tabel 11.4', 'Contoh keluaran API-07 pada situs deployed');
  ins.add(buildTable_(T.t4, [
    ['Persyaratan', 'Skill', 'Kemiripan', 'Alasan dari judge'],
    ['Menganalisis kerentanan aplikasi web', 'OWASP Top 10', '0,85', 'The skill OWASP Top 10 covers web application vulnerabilities analysis.'],
    ['memahami OWASP Top 10', 'OWASP Top 10', '0,78', 'The skill OWASP Top 10 directly matches the requirement.'],
    ['melakukan pengujian keamanan dasar', 'Web Security Testing', '0,85', 'Web Security Testing includes basic penetration testing.'],
    ['memantau log dengan SIEM', 'Belum tercakup', '-', 'No skill covers SIEM log monitoring.'],
  ]));

  H2('11.4 Kontribusi dua teknologi');
  P('Blockchain. Registry di Base Sepolia menjadi sumber kebenaran untuk integritas, otorisasi penerbit, dan status. Tiga uji pembeda membuktikan bahwa basis data biasa tidak dapat menggantikannya: mengubah isi kredensial di basis data tetap menghasilkan TAMPERED (TC-05), mengembalikan status di basis data ke aktif setelah dicabut tetap menghasilkan REVOKED pada 5 dari 5 verifikasi (TC-06), dan akun penerbit lain yang memanggil revokeCredential langsung pada kontrak ditolak dengan NotOriginalIssuer (TC-14). TC-16 menambahkan bukti keempat: setelah pemilik registry menonaktifkan ISS-002, kredensialnya terbaca ISSUER_UNAUTHORIZED. Inspeksi on-chain (TC-11) hanya menemukan komitmen, penerbit, status, waktu, dan issuerActive, tanpa nama, holderRef, judul program, maupun kriteria.', 'Blockchain.');
  P('AI. AMS memakai dua tahap. Embedding gemini-embedding-001 menghitung kemiripan setiap pasangan persyaratan dan skill terverifikasi, lalu judge gemini-3.1-flash-lite memutuskan, di antara skill dengan kemiripan 0,60 atau lebih, skill mana yang mencakup tiap persyaratan dan menuliskan alasannya. Tahap judge ditambahkan karena embedding saja tidak dapat membaca negasi, misalnya "tidak wajib", dan sulit membedakan teknologi yang mirip. Judge dipilih lewat evaluasi pada gold set terkunci berisi 101 butir sintetis (62 dev dan 39 uji). Aturan pemilihan ditetapkan sebelum model dijalankan, dan split uji tidak dipakai untuk memilih apa pun (Tabel 11.5).', 'AI.');
  CAP('Tabel 11.5', 'Hasil evaluasi pencocokan skill pada split uji (39 butir)');
  ins.add(buildTable_(T.t5, [
    ['Varian', 'Precision', 'Recall', 'F1', 'Negasi dan lintas bahasa'],
    ['Embedding saja, ambang 0,72 (rancangan awal)', '77,3%', '89,5%', '82,9%', '0 dari 5, 3 dari 5'],
    ['Embedding saja, ambang 0,71 (cadangan)', '75,0%', '94,7%', '83,7%', '0 dari 5, 4 dari 5'],
    ['Judge gemini-3.1-flash-lite, ambang kandidat 0,60 (dipakai)', '100%', '89,5%', '94,4%', '5 dari 5, 5 dari 5'],
    ['Judge gemini-3.5-flash-lite, ambang kandidat 0,60 (judge cadangan)', '100%', '79,0%', '88,2%', 'Tidak dilaporkan terpisah'],
  ]));
  P('Judge terpilih salah pada dua butir uji, keduanya persyaratan yang seharusnya tercakup (mengamankan jaringan nirkabel dan mendesain mockup di Figma). Dua run ulang tanpa cache memberi prediksi yang identik. Karena free tier Gemini kadang membalas 503 atau tidak menjawab, AMS memakai rantai cadangan: judge cadangan gemini-3.5-flash-lite bila judge utama tidak menjawab dalam 8 detik, lalu hasil judge yang tersimpan untuk posisi contoh, lalu embedding saja dengan ambang 0,71. Setiap jalur cadangan disebut pada modelVersion dan batasan. Bila kunci Gemini tidak ada, API-07 selalu mengembalikan 503 AI_UNAVAILABLE, sementara verifikasi tetap berjalan (TC-10).');
  P('Batas peran AI tetap dijaga. Hanya teks skill dan persyaratan yang dikirim ke Gemini, skill dibaca dari hasil verifikasi (VRS.getVerification) dan bukan dari data kiriman pemeriksa, keluaran selalu berlabel REKOMENDASI disertai batasan, dan tidak ada skor total kandidat.');

  H2('11.5 Hasil pengujian');
  P('Pengujian dijalankan dengan runner otomatis api/scripts/evidence.py terhadap stack deployed pada 20 November 2026 (API di Vercel, Supabase, registry Base Sepolia, dan Gemini). Runner yang sama juga dijalankan pada stack lokal (Hardhat dan PostgreSQL) dengan hasil 16 dari 16 lulus. Setiap skenario dicatat dalam format skenario, langkah atau masukan, hasil yang diharapkan, hasil aktual, status, dan bukti pada folder docs/evidence/deployed/ di repositori. Selain itu, 193 tes pytest dan 15 tes kontrak Hardhat lulus, serta lint, pemeriksaan tipe, dan build aplikasi web bersih.');
  CAP('Tabel 11.6', 'Hasil pengujian TC-01 sampai TC-16 pada stack deployed');
  ins.add(buildTable_(T.t7, [
    ['ID', 'Skenario', 'Langkah atau masukan', 'Hasil yang diharapkan', 'Hasil aktual', 'Status', 'Bukti'],
    ['TC-01', 'Penerbit terdaftar menerbitkan kredensial valid', 'admin.iss001 memanggil API-02 untuk HLD-2026-0007 dengan tiga skill katalog', '201, komitmen dan txHash tersimpan', '201, CRD-0007 terbit, komitmen off-chain sama dengan getRecord on-chain, txHash tersimpan', 'Lulus', 'TC-01.md'],
    ['TC-02', 'Akun bukan penerbit terdaftar menerbitkan', 'admin.unregistered memanggil API-02 dengan payload TC-01', '403 ISSUER_NOT_AUTHORIZED', '403 ISSUER_NOT_AUTHORIZED, jumlah kredensial tetap 6', 'Lulus', 'TC-02.md'],
    ['TC-03', 'Skill di luar katalog', 'API-02 dengan skill SK-999', '422 SKILL_NOT_IN_CATALOG', '422 SKILL_NOT_IN_CATALOG untuk SK-999', 'Lulus', 'TC-03.md'],
    ['TC-04', 'Verifikasi kredensial utuh tanpa admin', 'verifier.a mengirim shareToken ke API-06', '200, VALID', '200, VALID, ketiga pemeriksaan lolos, 0 peristiwa audit admin, hanya field dalam scope', 'Lulus', 'TC-04.md, Gambar 11.6'],
    ['TC-05', 'Isi kredensial diubah langsung di basis data', 'Judul program CRD-0008 diubah dengan SQL, lalu diverifikasi', '200, TAMPERED, data tidak ditampilkan', '200, TAMPERED, integrity FAIL, data kredensial tidak dikembalikan', 'Lulus', 'TC-05.md, Gambar 11.9'],
    ['TC-06', 'Verifikasi setelah pencabutan, status di basis data dikembalikan ke aktif', 'API-09 untuk CRD-0007, status di basis data diubah ke active, lalu diverifikasi', '200, REVOKED beserta alasan', '200, REVOKED dengan alasan "Data kelulusan keliru"', 'Lulus', 'TC-06.md, Gambar 11.8'],
    ['TC-07', 'Tautan kedaluwarsa', 'API-06 dengan tautan yang masa berlakunya lewat', '410 SHARE_LINK_EXPIRED', '410 SHARE_LINK_EXPIRED', 'Lulus', 'TC-07.md'],
    ['TC-08', 'Pencocokan setelah verifikasi VALID', 'API-07 dengan posisi Junior Security Analyst', 'Skill cocok, belum tercakup, REKOMENDASI, tanpa skor total', '200, REKOMENDASI, tiga pasangan cocok, SIEM belum tercakup, tanpa skor total', 'Lulus', 'TC-08.md, Tabel 11.4'],
    ['TC-09', 'Pencocokan memakai verifikasi bukan VALID', 'API-07 dengan verifikasi TAMPERED dari TC-05', '409 VERIFICATION_NOT_VALID', '409 VERIFICATION_NOT_VALID', 'Lulus', 'TC-09.md'],
    ['TC-10', 'Layanan AI dimatikan', 'API di-deploy ulang tanpa GEMINI_API_KEY, lalu API-07 dan API-06', 'API-07 503, API-06 tetap berfungsi', 'API-07 503 AI_UNAVAILABLE, API-06 200 VALID, setelah kunci dipasang lagi API-07 200', 'Lulus', 'TC-10.md'],
    ['TC-11', 'Inspeksi data on-chain', 'getRecord dan input transaksi dibaca di Base Sepolia', 'Hanya komitmen, penerbit, status', 'Tidak ada data pribadi, record berisi komitmen, ISS-001, active, waktu, issuerActive', 'Lulus', 'TC-11.md'],
    ['TC-12', 'Waktu verifikasi pada data uji', 'API-06 dijalankan 10 kali', 'Kurang dari 5 detik', 'Median 0,441 detik, maksimum 0,470 detik', 'Lulus', 'TC-12.md'],
    ['TC-13', 'Operasi penting dijalankan lalu audit dibaca', 'API-10 setelah terbit, bagikan, verifikasi, cocokkan, dan cabut', 'Tercatat tanpa payload sensitif', '49 peristiwa, tiap butir hanya time, actorRole, operation, objectId, outcome', 'Lulus', 'TC-13.md, Gambar 11.11'],
    ['TC-14', 'Penerbit lain memanggil revokeCredential langsung pada kontrak', 'Akun ISS-002 memanggil kontrak untuk CRD-0006 milik ISS-001', 'Transaksi ditolak, status tidak berubah', 'Revert NotOriginalIssuer, status tetap active', 'Lulus', 'TC-14.md'],
    ['TC-15', 'Pemeriksa memakai verificationId milik pemeriksa lain', 'verifier.b memakai verificationId milik verifier.a', '403 VERIFICATION_NOT_OWNED', '403 VERIFICATION_NOT_OWNED', 'Lulus', 'TC-15.md'],
    ['TC-16', 'Admin platform menonaktifkan penerbit, lalu kredensialnya diverifikasi', 'deactivateIssuer("ISS-002") dari akun pemilik registry, lalu API-06 untuk CRD-0009', '200, ISSUER_UNAUTHORIZED, issuerAuthorized FAIL', '200, ISSUER_UNAUTHORIZED, integrity PASS, issuerAuthorized FAIL, status ACTIVE', 'Lulus', 'TC-16.md, Gambar 11.10'],
  ]));
  P('Hasilnya 16 dari 16 skenario lulus. TC-14 dijalankan ulang secara terpisah setelah RPC publik sempat membalas 401 sementara, dan RGS kini mencoba ulang tiga kali sebelum mengembalikan 503. Bukti TC-08 direkam sebelum judge aktif, sehingga alasannya masih berasal dari templat embedding. Respons dengan judge ditunjukkan pada Tabel 11.4 dan Gambar 11.7.');

  H2('11.6 Capaian tujuan layanan');
  CAP('Tabel 11.7', 'Target T-01 sampai T-05 dan hasil terukur');
  ins.add(buildTable_(T.t4, [
    ['Tujuan', 'Target (Tabel 1.6)', 'Hasil terukur', 'Status'],
    ['T-01', 'Kurang dari 5 detik per verifikasi pada data uji', 'Median 0,441 detik, maksimum 0,470 detik dari 10 verifikasi, cold start 1,00 dan 1,56 detik (TC-12)', 'Tercapai'],
    ['T-02', 'Nol langkah admin pada jalur verifikasi', 'Nol: hanya token pemeriksa yang dipakai, peristiwa audit admin tetap 6 (TC-04)', 'Tercapai'],
    ['T-03', 'Hanya atribut yang diizinkan, tidak ada data pribadi on-chain', 'Pemeriksa hanya menerima field dalam scope, dan tidak ada data pribadi pada input transaksi maupun record (TC-04, TC-11)', 'Tercapai'],
    ['T-04', 'Ringkasan tersedia untuk setiap kredensial valid dan berlabel rekomendasi', '3 dari 3 pencocokan berlabel REKOMENDASI dengan batasan, tanpa skor total (TC-08), dan F1 judge 94,4% pada split uji', 'Tercapai'],
    ['T-05', '100% tampil dicabut, penerbit lain ditolak', '5 dari 5 verifikasi tetap REVOKED (TC-06), pencabutan oleh penerbit lain ditolak kontrak (TC-14)', 'Tercapai'],
  ]));

  H2('11.7 Keterbatasan prototipe');
  LI('Data seluruhnya sintetis. Label gold set disusun dengan bantuan agen AI pemrograman dan belum direview seluruh tim, butir yang ambigu dibuang, dan split uji hanya 39 butir sehingga satu butir setara 2,6 poin.');
  LI('Free tier Gemini membatasi embedding sekitar 100 teks per menit, dan model judge kadang overload. API-07 dapat membutuhkan sekitar 25 detik sebelum memakai cadangan, dan hasil judge tersimpan hanya tersedia untuk tiga posisi contoh.');
  LI('Pemecahan persyaratan pada kata "dan" dapat memotong frasa seperti "analisis dan visualisasi data".');
  LI('Login demo bersifat publik, sehingga siapa pun dapat menerbitkan atau mencabut kredensial sebagai ISS-001 memakai ETH testnet. Pendaftaran mandiri pemeriksa dan klaim holderRef oleh peserta belum ada (OD-11).');
  LI('Kunci penerbit disimpan kustodial sebagai secret API (OD-12), sehingga penerbit baru yang didaftarkan lewat API-01 belum dapat menerbitkan sebelum kuncinya ditambahkan.');
  LI('Pengiriman transaksi diserialkan per akun dengan advisory lock Postgres. Transaksi yang tidak tertambang dalam 60 detik menghasilkan 503 walaupun mungkin tetap tertambang, dan RPC publik Base Sepolia dapat membatasi permintaan.');
  LI('API berjalan serverless sehingga permintaan pertama setelah idle terkena cold start (sekitar 1 sampai 1,6 detik). Login bergantung pada Supabase Auth, batas laju login dibagi semua pengguna, dan gangguan Supabase menghasilkan 500 karena laporan tidak menamai kode untuk kasus ini.');
  LI('Notifikasi masih simulasi pada tabel notifications, penonaktifan penerbit belum memiliki endpoint, API-06 tidak mengembalikan tanggal pencabutan, setiap pembukaan tautan menyimpan verifikasi baru, dan versi koreksi (API-11, FR-11) baru berupa spesifikasi.');
  LI('Kondisi As-Is masih berbasis skenario dan empat responden wawancara, sehingga belum menjadi dasar klaim kuantitatif tentang penghematan waktu atau kepuasan pengguna.');

  H2('11.8 Rencana pengembangan');
  LI('Mereview label gold set bersama tim dan menambah butir dari deskripsi posisi nyata yang dianonimkan, lalu mengulang evaluasi tanpa mengubah aturan pemilihan.');
  LI('Membuat pendaftaran mandiri pemeriksa dan alur klaim holderRef oleh peserta (OD-11) untuk menggantikan login demo publik.');
  LI('Memindahkan kunci penerbit ke dompet masing-masing atau layanan pengelola kunci (OD-12), sehingga API tidak lagi memegang kunci.');
  LI('Menambah notifikasi surel nyata, endpoint penonaktifan penerbit untuk admin platform, dan versi koreksi kredensial (API-11).');
  LI('Memakai kuota Gemini berbayar atau khusus agar tidak bergantung pada jalur cadangan, dan menyimpan hasil verifikasi per tautan agar tidak tercatat berulang.');
  LI('Menguji coba bersama satu penyelenggara pelatihan kampus memakai data yang disetujui setelah kajian privasi (UU PDP), lalu mengukur ulang T-01 sampai T-05 dengan pengguna nyata.');
  LI('Mengkaji registry konsorsium atau jaringan L2 mainnet bila jumlah penerbit bertambah.');
  if (!hasPageBreak_(penutup)) body.insertPageBreak(ins.i);
}
function hasPageBreak_(p) { for (let k = 0; k < p.getNumChildren(); k++) if (p.getChild(k).getType() === ET.PAGE_BREAK) return true; return false; }

function conclusion_(body, T) {
  const anchor = mustPara_(body, /^Kelayakan dijaga/);
  const ins = new Ins_(body, body.getChildIndex(anchor));
  ins.add(para_(T.p, 'Pada Deliverable 3 (Bab XI), rancangan tersebut dibangun dan di-deploy di https://proofskill-two.vercel.app dengan registry di testnet Base Sepolia dan pencocokan skill memakai model Gemini. Seluruh 16 skenario uji lulus pada stack deployed, verifikasi berjalan dengan median 0,441 detik tanpa langkah admin, dan judge AI mencapai F1 94,4% pada split uji gold set. Kelima target T-01 sampai T-05 tercapai pada data uji sintetis.'));
}

function appendix_(body, T) {
  body.appendPageBreak();
  const ins = new Ins_(body, body.getNumChildren());
  ins.add(heading_(mustPara_(body, /^REFERENSI$/).copy(), 'REFERENSI', 'LAMPIRAN'));
  ins.add(para_(T.p, 'Lampiran berisi tautan ke prototipe, kode sumber, dan bukti pengujian. Berkas bukti berada di repositori publik dan dapat diperiksa ulang.'));
  ins.add(caption_(T.cap, 'Tabel L.1', 'Tautan dan berkas pendukung'));
  ins.add(buildTable_(T.t3, [
    ['Butir', 'Lokasi', 'Isi'],
    ['Situs web', 'https://proofskill-two.vercel.app', 'Prototipe yang dapat dicoba dengan login demo'],
    ['Dokumentasi API', 'https://proofskill-api.vercel.app/api/v1/docs', 'Spesifikasi OpenAPI dari FastAPI'],
    ['Kontrak registry', 'https://sepolia.basescan.org/address/0xFB11769EBD22fe1Ac40391227e6526ccf077D136', 'Kode kontrak terverifikasi dan riwayat transaksi'],
    ['Repositori', 'https://github.com/veinsan/proofskill', 'Kode sumber, PRD, arsitektur, dan rencana kerja'],
    ['Bukti uji deployed', 'https://github.com/veinsan/proofskill/tree/main/docs/evidence/deployed', 'TC-01 sampai TC-16 beserta permintaan dan respons'],
    ['Bukti uji lokal', 'https://github.com/veinsan/proofskill/tree/main/docs/evidence', 'TC-01 sampai TC-16 pada Hardhat dan PostgreSQL lokal, keluaran pytest'],
    ['Evaluasi AI', 'https://github.com/veinsan/proofskill/tree/main/docs/evidence/matching-eval', 'Gold set, hasil per varian, dan kesalahan judge'],
    ['Tangkapan layar', 'https://github.com/veinsan/proofskill/tree/main/docs/evidence/ui', '14 halaman portal pada situs deployed'],
    ['Video demo', '[isi tautan]', 'Rekaman alur utama sebagai cadangan presentasi'],
  ]));
}

function references_(body, T) {
  const add = (beforeRe, afterRe, text) => {
    const anchor = mustPara_(body, beforeRe || afterRe);
    const idx = body.getChildIndex(anchor) + (beforeRe ? 0 : 1);
    body.insertParagraph(idx, para_(T.ref, text));
  };
  add(/^BCA Sekuritas/, null, 'Base. Base Documentation: Base Sepolia testnet. https://docs.base.org');
  add(null, /^Good News from Indonesia/, 'Google. Gemini API Documentation: embeddings, structured output, dan model Gemini. https://ai.google.dev/gemini-api/docs');
  add(null, /^Suhardi dkk/, 'Supabase. Supabase Documentation: Database, Auth, dan Row Level Security. https://supabase.com/docs');
  add(/^W3C\. \(2025\)/, null, 'Vercel. Vercel Documentation: Next.js dan Python runtime. https://vercel.com/docs');
}
