/**
 * ProofSkill: brings the D1+D2 deck in line with the deployed website and adds the Deliverable 3 section.
 * Runs from a standalone Apps Script project and opens the deck by ID. Run slidesDryRun() first; it
 * changes nothing and logs every find that is missing. Then run slidesApplyAll() once.
 * The state before the run stays in File > Version history.
 */
const PRES_ID = '1WfNM9kEujELB3kGDd93bluzXbP0uFayLdAguLaKmoZk';
const RAW_S = 'https://raw.githubusercontent.com/veinsan/proofskill/docs/d3-report-sync/';
const ROYAL = '#2453D6', INK = '#0E1A3B';

function pres_() { return SlidesApp.openById(PRES_ID); }
function texts_(slide) {
  const out = [];
  slide.getPageElements().forEach((el) => {
    const ty = el.getPageElementType();
    if (ty === SlidesApp.PageElementType.SHAPE) out.push(el.asShape().getText().asString());
    if (ty === SlidesApp.PageElementType.TABLE) {
      const t = el.asTable();
      for (let r = 0; r < t.getNumRows(); r++) for (let c = 0; c < t.getNumColumns(); c++) { try { out.push(t.getCell(r, c).getText().asString()); } catch (e) { /* merged cell */ } }
    }
  });
  return out.join('\n');
}
/** Finds a slide by the start of its title text, or by index when `key` is a number. */
function slide_(pres, key) {
  const slides = pres.getSlides();
  if (typeof key === 'number') return slides[key < 0 ? slides.length + key : key];
  // Only the title area counts: the section labels at the bottom repeat on every slide.
  const s = slides.find((sl) => sl.getShapes().some((sh) => sh.getTop() < 60 && sh.getText().asString().trim().indexOf(key) === 0));
  if (!s) throw new Error('Slide not found: ' + key);
  return s;
}
function table_(slide, i) { return slide.getTables()[i || 0]; }
function rowOf_(t, first) {
  for (let r = 0; r < t.getNumRows(); r++) if (t.getCell(r, 0).getText().asString().trim().indexOf(first) === 0) return r;
  throw new Error('Row not found: ' + first);
}
function setCell_(t, r, c, text) { t.getCell(r, c).getText().setText(text); }

// [slide key, find, replace]. A slide key is a title prefix or an index (0 = cover, -1 = closing).
const SL = [
  [0, 'Deliverable 1 & 2 Identifikasi dan Desain Layanan, Desain Proses (BPMN), dan Desain Teknis (SoaML, REST API, Rencana Prototipe)', 'Deliverable 1, 2 & 3 Identifikasi dan Desain Layanan, Desain Proses (BPMN), Desain Teknis (SoaML, REST API), serta Prototipe dan Pengujian'],
  ['Tim Penyusun', 'membagi seluruh bab D1 dan D2 secara merata', 'membagi seluruh bab D1, D2, dan D3'],
  ['Executive Summary', 'Jawabannya registry blockchain dan ringkasan skill AI, verifikasi < 5 detik tanpa admin', 'Jawabannya registry blockchain dan ringkasan skill AI, terbukti di prototipe: verifikasi 0,44 detik tanpa admin'],
  ['Executive Summary', '< 5 detik', '0,44 detik'],
  ['Executive Summary', 'waktu verifikasi pada data uji', 'median verifikasi, stack deployed'],
  ['Executive Summary', 'D2: BPMN, SoaML, 12 endpoint, 15 uji', 'D2: BPMN, SoaML, 14 endpoint, 16 uji'],
  ['Executive Summary', 'sampai desain proses dan desain teknis yang siap dibangun (D2)', 'sampai desain proses dan desain teknis (D2), lalu prototipe yang di-deploy dan diuji (D3)'],
  ['Executive Summary', 'Kesiapan Uji (D3)', 'Hasil Uji (D3)'],
  ['Executive Summary', '15 skenario', '16/16 skenario'],
  ['Executive Summary', 'uji siap dijalankan di D3', 'uji lulus di stack deployed'],
  ['Executive Summary', 'Target adalah kriteria penerimaan rancangan, bukan klaim kinerja, angka dilaporkan setelah prototipe diukur di D3.', 'Terukur di stack deployed dengan data sintetis: median verifikasi 0,441 detik, 0 langkah admin, 5/5 status cabut terbaca.'],
  ['D1 - Konteks - Studi kasus', 'Belum ada wawancara.', 'Wawancara empat responden (R1-R4) dilakukan di D2.'],
  ['D1 - Konteks - Alasan teknologi', 'Embedding multibahasa memetakan', 'Embedding dan judge Gemini memetakan'],
  ['D1 - Kebutuhan - Akar masalah', 'wawancara belum dilakukan, jadi 5 Whys adalah dugaan mekanisme', 'wawancara D2 baru memberi indikasi awal, jadi 5 Whys tetap dugaan mekanisme'],
  ['D1 - Kebutuhan - Fungsional (1/2)', 'di blockchain lokal', 'di blockchain (testnet Base Sepolia)'],
  ['D1 - Kebutuhan - Nonfungsional', 'Kinerja prototipe lokal', 'Kinerja prototipe'],
  ['D1 - Desain Layanan - Service Blueprint To-Be', 'Halaman hasil: VALID, REVOKED, atau TAMPERED', 'Halaman hasil: VALID, REVOKED, TAMPERED, atau ISSUER_UNAUTHORIZED'],
  ['D1 - Desain Layanan - Service Blueprint To-Be', 'Notifikasi surel dan halaman kredensial', 'Notifikasi surel (disimulasikan) dan halaman kredensial'],
  ['D1 - Desain Layanan - Service Blueprint To-Be', 'Model embedding, katalog skill, log keluaran', 'Embedding dan judge Gemini, katalog skill, log keluaran'],
  ['D2 - BPMN - To-Be 3', 'hasilnya VALID, REVOKED, atau TAMPERED beserta alasannya', 'hasilnya VALID, REVOKED, TAMPERED, atau ISSUER_UNAUTHORIZED beserta alasannya'],
  ['D2 - SoaML - Identifikasi Layanan', 'issueCredential, getCredential', 'issueCredential, getCredential, listOwnCredentials'],
  ['D2 - SoaML - Identifikasi Layanan', 'matchSkills (embedding multibahasa)', 'matchSkills (embedding + judge Gemini)'],
  ['D2 - SoaML - Services Architecture', '19 operasi', '20 operasi'],
  ['D2 - REST API - Endpoint', 'dua belas endpoint REST', 'empat belas endpoint REST'],
  ['D2 - REST API - Endpoint', '7 lainnya', '9 lainnya'],
  ['D2 - REST API - Endpoint', 'token, issuers, credential, skills, audit-logs, share-link, versions', 'token, issuers, credential, skills, audit-logs, share-link, versions, daftar milik sendiri (API-12, 13)'],
  ['D2 - Prototipe - Rencana Implementasi', 'dengan stack Next.js, FastAPI, PostgreSQL, Hardhat, dan embedding lokal', 'yang dibangun dengan Next.js, FastAPI, Supabase, Base Sepolia, dan Gemini'],
  ['D2 - Prototipe - Rencana Implementasi', 'Stack usulan', 'Stack yang dipakai'],
  ['D2 - Prototipe - Rencana Implementasi', 'PostgreSQL', 'Supabase Postgres + Auth'],
  ['D2 - Prototipe - Rencana Implementasi', 'Metadata off-chain dan audit log', 'Metadata off-chain, audit, login'],
  ['D2 - Prototipe - Rencana Implementasi', 'Hardhat + Solidity', 'Solidity di Base Sepolia'],
  ['D2 - Prototipe - Rencana Implementasi', 'Kontrak ProofSkillRegistry', 'ProofSkillRegistry (uji: Hardhat)'],
  ['D2 - Prototipe - Rencana Implementasi', 'Embedding multibahasa', 'Gemini API'],
  ['D2 - Prototipe - Rencana Implementasi', 'Pencocokan skill, dijalankan lokal', 'Embedding + judge pencocokan skill'],
  ['D2 - Prototipe - Pengujian', 'Lima belas skenario uji untuk D3', 'Enam belas skenario uji untuk D3 (TC-16 ditambahkan saat implementasi)'],
  ['D2 - Prototipe - Pengujian', 'TC-15 verificationId milik orang lain (403)', 'TC-15 verificationId milik orang lain (403), TC-16 penerbit dinonaktifkan (ISSUER_UNAUTHORIZED)'],
  ['D2 - Prototipe - Pengujian', 'Web & 15 uji', 'Web & 16 uji'],
  ['Kesimpulan', 'Target D3', 'Hasil D3'],
  ['Kesimpulan', '< 5 detik dan 0 langkah admin per verifikasi', '0,44 detik dan 0 langkah admin per verifikasi (terukur)'],
  ['Kesimpulan', '< 5 detik', '0,44 detik'],
  ['Kesimpulan', '15 skenario', '16/16 lulus'],
  ['Kesimpulan', 'uji TC-01 sampai TC-15', 'uji TC-01 sampai TC-16'],
  ['Arsitektur Prototipe', 'Aplikasi web (usulan: Next.js)', 'Aplikasi web (Next.js, Vercel)'],
  ['Arsitektur Prototipe', 'REST API (usulan: FastAPI, /api/v1)', 'REST API (FastAPI, Vercel, /api/v1)'],
  ['Arsitektur Prototipe', 'Basis data off-chain (PostgreSQL)', 'Basis data off-chain (Supabase Postgres)'],
  ['Arsitektur Prototipe', 'web3 / JSON-RPC', 'JSON-RPC, transaksi ditandatangani API'],
  ['Arsitektur Prototipe', 'Blockchain lokal (Hardhat)', 'Blockchain: testnet Base Sepolia'],
  ['Arsitektur Prototipe', 'revokeCredential, getRecord. Hanya hash, penerbit, status', 'revokeCredential, getRecord, deactivateIssuer. Hanya hash, penerbit, status'],
  ['Arsitektur Prototipe', 'pemanggilan lokal', 'REST, Gemini API'],
  ['Arsitektur Prototipe', 'Modul AI (embedding multibahasa)', 'Modul AI (Gemini: embedding + judge)'],
  ['Arsitektur Prototipe', 'Stack adalah usulan yang dapat disesuaikan tim.', 'Stack sesuai deployment D3.'],
  ['Arsitektur Prototipe', 'blockchain lokal (hash, penerbit, status), modul AI', 'blockchain testnet Base Sepolia (hash, penerbit, status), modul AI Gemini'],
  ['Daftar Endpoint', 'Cabut tautan (opsional)', 'Cabut tautan'],
  ['Daftar Endpoint', 'Dua belas endpoint (API-00 sampai API-11)', 'Empat belas endpoint (API-00 sampai API-13)'],
  ['Skenario Uji D3', 'Lima belas skenario uji (TC-01 sampai TC-15)', 'Enam belas skenario uji (TC-01 sampai TC-16)'],
  ['Jadwal & Risiko', 'TC-01 sampai TC-15', 'TC-01 sampai TC-16'],
  [-1, 'Deliverable 1 & 2', 'Deliverable 1, 2 & 3'],
];

function slidesDryRun() {
  const pres = pres_();
  let bad = 0;
  SL.forEach(([key, f]) => {
    try { if (texts_(slide_(pres, key)).indexOf(f) < 0) { bad++; console.log('MISSING on ' + key + ': ' + f.slice(0, 80)); } }
    catch (e) { bad++; console.log(String(e)); }
  });
  ['Bagian 2', 'D2 - REST API - Endpoint', 'D2 - Prototipe - Pengujian', 'Kesimpulan', 'Daftar Endpoint', 'Skenario Uji D3', 'Tim Penyusun'].forEach((k) => {
    try { const s = slide_(pres, k); console.log('ok ' + k + ' (#' + (pres.getSlides().indexOf(s) + 1) + ', tables ' + s.getTables().length + ')'); } catch (e) { bad++; console.log(String(e)); }
  });
  try { UrlFetchApp.fetch(RAW_S + 'docs/figures/arsitektur-deployed.png'); console.log('image URL ok'); } catch (e) { bad++; console.log('IMAGE URL FAILED: ' + e); }
  console.log(bad ? bad + ' problem(s)' : 'dry run clean');
}

function slidesApplyAll() {
  const pres = pres_();
  SL.forEach(([key, f, r]) => {
    const n = slide_(pres, key).replaceAllText(f, r);
    if (!n) console.log('NOT REPLACED on ' + key + ': ' + f.slice(0, 80));
  });
  tableEdits_(pres);
  d3Section_(pres);
  console.log('done');
}

function tableEdits_(pres) {
  // Service Interface: CredentialIssuanceService gains listOwnCredentials (API-12, API-13).
  const ops = slide_(pres, 'Service Interface').getShapes().find((sh) => sh.getText().asString().indexOf('getCredential(credentialId)') >= 0);
  ops.getText().appendText('\nlistOwnCredentials(limit, offset): CredentialList\n[FR-05]');

  // Rencana Implementasi: endpoints per feature.
  const t46 = table_(slide_(pres, 'D2 - Prototipe - Rencana Implementasi'));
  setCell_(t46, rowOf_(t46, 'F-03'), 1, 'API-03, 04, 05, 12');
  setCell_(t46, rowOf_(t46, 'F-05'), 1, 'API-09, 13');

  // Daftar Endpoint: API-12 and API-13 share one row so the table still fits the slide.
  const sEp = slide_(pres, 'Daftar Endpoint');
  const tEp = table_(sEp);
  const rowEp = tEp.appendRow();
  ['API-12, 13', 'GET /holders/me/credentials, GET /issuers/me/credentials', 'Daftar milik sendiri', 'holder, issuer_admin', 'CIS.listOwnCredentials']
    .forEach((v, j) => rowEp.getCell(j).getText().setText(v));
  sEp.getTables()[0].setTop(46);

  // Skenario Uji D3: TC-16.
  const sTc = slide_(pres, 'Skenario Uji D3');
  const tTc = table_(sTc);
  const rowTc = tTc.appendRow();
  ['TC-16', 'Admin platform menonaktifkan penerbit, lalu verifikasi', '200, ISSUER_UNAUTHORIZED', 'API-06, ditambahkan saat implementasi']
    .forEach((v, j) => rowTc.getCell(j).getText().setText(v));
  tTc.setTop(46);
}

// ---------- Deliverable 3 section ----------
function font_() { return 'Poppins'; }
function clearContent_(slide) {
  slide.getPageElements().forEach((el) => { const t = el.getTop(); if (t >= 76 && t < 372) el.remove(); });
}
function setHead_(slide, title, subtitle) {
  slide.getShapes().forEach((sh) => {
    const t = sh.getTop(), l = sh.getLeft();
    if (l < 40 && sh.getWidth() > 300 && t < 10) sh.getText().setText(title);
    else if (l < 40 && sh.getWidth() > 300 && t >= 15 && t < 40) sh.getText().setText(subtitle);
  });
}
function text_(slide, text, l, t, w, h, size, opts) {
  const o = opts || {};
  const box = slide.insertTextBox(text, l, t, w, h);
  const st = box.getText().getTextStyle();
  st.setFontFamily(font_()).setFontSize(size).setForegroundColor(o.color || INK).setBold(!!o.bold);
  if (o.fill) box.getFill().setSolidFill(o.fill);
  if (o.center) box.getText().getParagraphStyle().setParagraphAlignment(SlidesApp.ParagraphAlignment.CENTER);
  return box;
}
function image_(slide, path, l, t, w, h) {
  const blob = UrlFetchApp.fetch(RAW_S + path).getBlob();
  const im = slide.insertImage(blob);
  const k = Math.min(w / im.getWidth(), h / im.getHeight());
  const iw = im.getWidth() * k, ih = im.getHeight() * k;
  im.setWidth(iw).setHeight(ih).setLeft(l + (w - iw) / 2).setTop(t);
  im.getBorder().setWeight(0.75).getLineFill().setSolidFill('#C9D4F2');
  return im;
}
function takeaway_(slide, text) {
  text_(slide, 'Key Takeaways', 22, 330, 200, 16, 11, { bold: true, color: ROYAL });
  text_(slide, text, 22, 347, 676, 24, 9);
}
/** Moves a slide to just before Kesimpulan (the insertion index counts slides before the move). */
function place_(pres, s) {
  const ids = pres.getSlides().map((x) => x.getObjectId());
  s.move(ids.indexOf(KES_ID));
}
let KES_ID = null;
function newSlide_(pres, tmpl, title, subtitle) {
  const s = tmpl.duplicate();
  place_(pres, s);
  clearContent_(s);
  setHead_(s, title, subtitle);
  s.replaceAllText('Desain Teknis', 'Prototipe & Uji');
  return s;
}

function d3Section_(pres) {
  const divider = slide_(pres, 'Bagian 2');
  const content = slide_(pres, 'D2 - REST API - Endpoint');
  const tcPlan = slide_(pres, 'Skenario Uji D3');
  KES_ID = slide_(pres, 'Kesimpulan').getObjectId(); // the D3 section goes right before Kesimpulan

  const d = divider.duplicate(); place_(pres, d);
  d.replaceAllText('Bagian 2', 'Bagian 3');
  d.replaceAllText('DELIVERABLE 2', 'DELIVERABLE 3');

  // Arsitektur deployed
  let s = newSlide_(pres, content, 'D3 - Prototipe - Arsitektur deployed', 'Rancangan D2 dibangun dan di-deploy: web dan API di Vercel, data dan login di Supabase, registry di testnet Base Sepolia, pencocokan skill dengan model Gemini');
  image_(s, 'docs/figures/arsitektur-deployed.png', 22, 80, 470, 245);
  text_(s, 'proofskill-two.vercel.app\nLogin demo sekali klik untuk 6 akun sintetis\n\n13 endpoint dibangun\nAPI-00 sampai API-10, API-12, API-13 (API-11 hanya spesifikasi)\n\nKontrak 0xFB11…D136\nTerverifikasi di Basescan, hanya komitmen, penerbit, status', 505, 84, 195, 240, 9.5);
  takeaway_(s, 'Kontrak API, kode galat, dan enum tetap sama dengan laporan Bab IX. Yang ditambahkan saat implementasi: API-12 dan API-13 (daftar milik sendiri), TC-16, peran platform_admin, kode ISSUER_ALREADY_REGISTERED.');

  // Demo penerbit dan peserta
  s = newSlide_(pres, content, 'D3 - Demo - Penerbitan & berbagi', 'Penerbit menerbitkan kredensial yang langsung tercatat di registry, lalu peserta memilih field yang dibagikan dan masa berlaku tautannya');
  image_(s, 'docs/figures/slides/issuer-credential.jpg', 22, 82, 330, 206);
  image_(s, 'docs/figures/slides/holder-share-link.jpg', 368, 82, 330, 206);
  text_(s, 'Portal penerbit: pass ACTIVE, commit dan tx di Base Sepolia, panel cabut (API-02, 03, 09)', 22, 292, 330, 28, 8.5, { center: true });
  text_(s, 'Portal peserta: scope, masa berlaku, tautan dan QR, cabut tautan (API-04, 05, 12)', 368, 292, 330, 28, 8.5, { center: true });
  takeaway_(s, 'Hash SHA-256 ber-nonce dihitung API, hanya komitmen, penerbit, dan status yang masuk ke chain. Scope disimpan di server, jadi pemeriksa tidak bisa memperluasnya.');

  // Demo verifikasi dan skill fit
  s = newSlide_(pres, content, 'D3 - Demo - Verifikasi & ringkasan skill', 'Pemeriksa membuka tautan dan langsung melihat VALID beserta tiga pemeriksaan, lalu ringkasan skill berlabel REKOMENDASI dengan alasan dari judge AI');
  image_(s, 'docs/figures/slides/verifier-valid.jpg', 22, 82, 420, 240);
  image_(s, 'docs/figures/slides/verifier-skill-fit.jpg', 470, 80, 228, 245);
  takeaway_(s, 'API-06 berjalan 0,44 detik (median) tanpa admin. API-07 memakai gemini-embedding-001 lalu judge gemini-3.1-flash-lite: 3 pasangan cocok, SIEM belum tercakup, tanpa skor total.');

  // Hasil tidak sah
  s = newSlide_(pres, content, 'D3 - Demo - Hasil tidak sah', 'Hasil yang tidak sah tetap dijawab 200 dengan alasan, data disembunyikan bila perlu, dan ringkasan skill tidak ditawarkan');
  [['verifier-revoked', 'REVOKED: dicabut penerbit, alasan ditampilkan (TC-06)'], ['verifier-tampered', 'TAMPERED: data diubah di basis data, isi disembunyikan (TC-05)'], ['verifier-issuer-unauthorized', 'ISSUER_UNAUTHORIZED: penerbit dinonaktifkan di registry (TC-16)']]
    .forEach(([f, cap], i) => {
      image_(s, 'docs/figures/slides/' + f + '.jpg', 22 + i * 228, 92, 218, 122);
      text_(s, cap, 22 + i * 228, 222, 218, 40, 8.5, { center: true });
    });
  takeaway_(s, 'Kebenaran dibandingkan dengan registry, bukan dengan basis data yang bisa diubah satu pihak: mengubah data atau status di basis data tidak mengubah hasil verifikasi.');

  // Kontribusi teknologi
  s = newSlide_(pres, content, 'D3 - Kontribusi Blockchain & AI', 'Blockchain tidak tergantikan basis data biasa (tiga uji pembeda lulus), dan judge AI menaikkan F1 pencocokan dari 82,9% ke 94,4% pada split uji gold set');
  text_(s, 'Blockchain (Base Sepolia)', 22, 82, 330, 18, 11, { bold: true, color: ROYAL });
  text_(s, 'TC-05: isi diubah di basis data, tetap TAMPERED\nTC-06: status dikembalikan ke aktif, 5/5 tetap REVOKED\nTC-14: penerbit lain revoke langsung ke kontrak, ditolak NotOriginalIssuer\nTC-16: penerbit dinonaktifkan, ISSUER_UNAUTHORIZED\nTC-11: tidak ada data pribadi on-chain', 22, 104, 330, 150, 9.5);
  text_(s, 'AI (Gemini)', 368, 82, 330, 18, 11, { bold: true, color: ROYAL });
  [['82,9% → 94,4%', 'F1 split uji (39 butir)'], ['0/5 → 5/5', 'persyaratan bernegasi'], ['3/5 → 5/5', 'lintas bahasa'], ['100%', 'precision judge']]
    .forEach(([big, small], i) => {
      const x = 368 + (i % 2) * 168, y = 104 + Math.floor(i / 2) * 74;
      text_(s, big + '\n' + small, x, y, 160, 66, 10, { fill: '#EEF2FC', center: true });
    });
  text_(s, 'Judge dipilih dengan aturan F1 dev yang dikunci sebelum model dijalankan. Cadangan: judge gemini-3.5-flash-lite, hasil tersimpan, lalu embedding 0,71.', 368, 256, 330, 40, 8.5);
  takeaway_(s, 'AI hanya menerima teks skill dan persyaratan, membaca skill dari hasil verifikasi, dan selalu berlabel REKOMENDASI. Bila AI mati, hanya API-07 yang 503 dan verifikasi tetap jalan (TC-10).');

  // Hasil pengujian: a copy of the TC plan slide with actual results
  s = tcPlan.duplicate(); place_(pres, s);
  const tR = s.getTables()[0];
  const actual = {
    'TC-01': ['201, CRD-0007 terbit, komitmen = getRecord', 'Lulus'], 'TC-02': ['403 ISSUER_NOT_AUTHORIZED, tidak ada yang terbit', 'Lulus'],
    'TC-03': ['422 SKILL_NOT_IN_CATALOG (SK-999)', 'Lulus'], 'TC-04': ['200 VALID, 0 langkah admin', 'Lulus'],
    'TC-05': ['200 TAMPERED, data tidak dikembalikan', 'Lulus'], 'TC-06': ['200 REVOKED + alasan', 'Lulus'],
    'TC-07': ['410 SHARE_LINK_EXPIRED', 'Lulus'], 'TC-08': ['200 REKOMENDASI, tanpa skor total', 'Lulus'],
    'TC-09': ['409 VERIFICATION_NOT_VALID', 'Lulus'], 'TC-10': ['API-07 503, API-06 200 VALID', 'Lulus'],
    'TC-11': ['Tanpa data pribadi on-chain', 'Lulus'], 'TC-12': ['Median 0,441 s, maks 0,470 s', 'Lulus'],
    'TC-13': ['49 peristiwa, tanpa payload sensitif', 'Lulus'], 'TC-14': ['Revert NotOriginalIssuer, status tetap', 'Lulus'],
    'TC-15': ['403 VERIFICATION_NOT_OWNED', 'Lulus'], 'TC-16': ['200 ISSUER_UNAUTHORIZED', 'Lulus'],
  };
  setCell_(tR, 0, 2, 'Hasil aktual (stack deployed)');
  setCell_(tR, 0, 3, 'Status');
  for (let r = 1; r < tR.getNumRows(); r++) {
    const id = tR.getCell(r, 0).getText().asString().trim();
    if (actual[id]) { setCell_(tR, r, 2, actual[id][0]); setCell_(tR, r, 3, actual[id][1]); }
  }
  s.replaceAllText('Skenario Uji D3', 'D3 - Hasil Pengujian');
  s.replaceAllText('Enam belas skenario uji (TC-01 sampai TC-16) memberi cara pembuktian bagi tiap tujuan dan kebutuhan: alur sukses, galat, kinerja, privasi, audit', '16 dari 16 skenario lulus pada stack deployed (20 Nov 2026) dan lokal, ditambah 193 tes API dan 15 tes kontrak. Bukti: docs/evidence/deployed');

  // Capaian, keterbatasan, rencana
  s = newSlide_(pres, content, 'D3 - Capaian, keterbatasan & rencana', 'Kelima target layanan tercapai pada data uji sintetis, dengan keterbatasan yang dicatat terbuka dan rencana pengembangan berikutnya');
  [['T-01', '0,441 s', 'median verifikasi (< 5 s)'], ['T-02', '0', 'langkah admin'], ['T-03', '0', 'data pribadi on-chain'], ['T-04', '3/3', 'berlabel REKOMENDASI'], ['T-05', '5/5', 'tetap REVOKED']]
    .forEach(([id, big, small], i) => text_(s, id + '\n' + big + '\n' + small, 22 + i * 136, 82, 128, 62, 9.5, { fill: '#EEF2FC', center: true }));
  text_(s, 'Keterbatasan', 22, 154, 330, 18, 11, { bold: true, color: ROYAL });
  text_(s, '• Data sintetis, label gold set belum direview tim (39 butir uji)\n• Free tier Gemini kadang overload, ada jalur cadangan\n• Kunci penerbit kustodial di API (OD-12)\n• Login demo publik, belum ada daftar mandiri (OD-11)\n• Notifikasi masih simulasi, API-11 hanya spesifikasi', 22, 174, 330, 150, 9);
  text_(s, 'Rencana pengembangan', 368, 154, 330, 18, 11, { bold: true, color: ROYAL });
  text_(s, '• Review gold set bersama tim dan data posisi nyata\n• Daftar mandiri pemeriksa dan klaim holderRef\n• Kunci penerbit di dompet sendiri atau KMS\n• Surel nyata, endpoint nonaktifkan penerbit, versi koreksi\n• Uji coba dengan penyelenggara kampus setelah kajian UU PDP', 368, 174, 330, 150, 9);
  takeaway_(s, 'Prototipe membuktikan alur terbit, bagikan, verifikasi, cocokkan, dan cabut berjalan ujung ke ujung di stack publik, dengan peran blockchain dan AI yang terukur.');

  // Team table for D3, appended right after the team slide
  const team = slide_(pres, 'Tim Penyusun');
  const t3 = team.duplicate();
  const tt = t3.getTables()[0];
  setCell_(tt, 0, 2, 'Deliverable 3');
  setCell_(tt, 0, 4, 'D3');
  const d3 = { '18224061': ['Implementasi dan deployment (kontrak, API, web, Supabase, Base Sepolia, Gemini), pengujian, evaluasi AI', '[isi]'], '18224005': ['Redesign antarmuka web (liquid glass, landing, login, aset 3D)', '[isi]'] };
  for (let r = 1; r < tt.getNumRows(); r++) {
    const nim = tt.getCell(r, 1).getText().asString().trim();
    if (!nim) continue;
    setCell_(tt, r, 2, d3[nim] ? d3[nim][0] : '[isi]');
    setCell_(tt, r, 4, d3[nim] ? d3[nim][1] : '[isi]');
  }
  tt.getColumn(5).remove();
  tt.getColumn(3).remove();
  t3.replaceAllText('Tim Penyusun - Pembagian tugas', 'Tim Penyusun - Pembagian tugas D3');
}
