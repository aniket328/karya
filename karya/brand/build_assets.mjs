// Karya brand assets -> every Plane asset path (same file names, so upstream merges never touch call sites).
// Run: node karya/brand/build_assets.mjs   (needs `playwright` + system Chrome; ICO via python3 PIL)
import { chromium } from 'playwright';
import { writeFileSync } from 'fs';
import { execFileSync } from 'child_process';
import path from 'path';
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const C = '#ff7a59', TILE = '#1c0f0b';
const glyph = (c = C) => `<rect x="24" y="38" width="36" height="36" rx="9" stroke="${c}" stroke-width="5" opacity="0.55"/><path d="M33 56L42 65L67 37" stroke="${c}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/><circle cx="76" cy="27" r="5" fill="${c}"/>`;
const tile = (s) => `<svg xmlns="http://www.w3.org/2000/svg" width="${s}" height="${s}" viewBox="0 0 100 100" fill="none"><rect width="100" height="100" rx="22" fill="${TILE}"/>${glyph()}</svg>`;
const FONT = `Inter, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif`;
const horiz = (w, h, text, glyphColor = C, withTile = true) => `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w * 100 / h} 100" fill="none">${withTile ? `<rect width="100" height="100" rx="22" fill="${TILE}"/>` : ''}<g>${glyph(glyphColor)}</g><text x="122" y="68" font-family="${FONT}" font-size="56" font-weight="650" letter-spacing="-1.5" fill="${text}">Karya</text></svg>`;
const og = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630"><rect width="1200" height="630" fill="#0b0908"/><circle cx="980" cy="120" r="320" fill="${C}" opacity="0.07"/><g transform="translate(110 175) scale(1.9)"><rect width="100" height="100" rx="22" fill="${TILE}"/><g fill="none">${glyph()}</g></g><text x="340" y="290" font-family="${FONT}" font-size="120" font-weight="700" letter-spacing="-4" fill="#f5f5f4">Karya</text><text x="700" y="290" font-family="'Kohinoor Devanagari','Noto Sans Devanagari',sans-serif" font-size="80" fill="${C}">कार्य</text><text x="344" y="350" font-family="${FONT}" font-size="34" fill="#a8a29e">Every piece of work, one place.</text><text x="112" y="545" font-family="${FONT}" font-size="22" letter-spacing="5" fill="#78716c">BY CWI STUDIO</text></svg>`;

const out = []; const png = (svg, w, h, files, transparent = true) => out.push({ svg, w, h, files, transparent });
const svgf = (svg, files) => files.forEach(f => writeFileSync(path.join(ROOT, f), svg));
for (const app of ['web', 'admin', 'space']) {
  png(tile(192), 192, 192, [`apps/${app}/public/favicon/android-chrome-192x192.png`]);
  png(tile(512), 512, 512, [`apps/${app}/public/favicon/android-chrome-512x512.png`]);
  png(tile(180), 180, 180, [`apps/${app}/app/assets/favicon/apple-touch-icon.png`]);
  png(tile(32), 32, 32, [`apps/${app}/app/assets/favicon/favicon-32x32.png`]);
  png(tile(16), 16, 16, [`apps/${app}/app/assets/favicon/favicon-16x16.png`]);
  png(tile(48), 48, 48, [`apps/${app}/app/assets/favicon/favicon-48.tmp.png`]);
}
png(tile(1024), 1024, 1024, ['apps/web/public/plane-logos/plane-mobile-pwa.png']);
for (const app of ['web', 'space']) {
  png(horiz(269, 60, '#1c1917'), 269, 60, [`apps/${app}/app/assets/plane-logos/black-horizontal-with-blue-logo.png`]);
  png(horiz(269, 60, '#fafaf9'), 269, 60, [`apps/${app}/app/assets/plane-logos/white-horizontal-with-blue-logo.png`]);
  png(tile(276), 276, 276, [`apps/${app}/app/assets/plane-logos/blue-without-text.png`]);
  svgf(horiz(178, 40, '#ffffff', '#ffffff', false), [`apps/${app}/app/assets/plane-logos/white-horizontal.svg`]);
}
png(tile(276), 276, 276, ['apps/space/app/assets/plane-logos/blue-without-text-new.png']);
png(og, 1200, 630, ['apps/web/app/assets/og-image.png', 'apps/web/public/og-image.png'], false);
// email logos, served by the web app at https://karya.cwistudio.in/karya/email-logo-*.png (templates link there)
png(horiz(300, 64, '#ffffff'), 300, 64, ['apps/web/public/karya/email-logo-white.png']);
png(horiz(300, 64, '#1c1917'), 300, 64, ['apps/web/public/karya/email-logo-dark.png']);
svgf(tile(155), ['apps/space/app/assets/plane-logo.svg']);
svgf(horiz(253, 53, '#1c1917'), ['packages/propel/public/plane-lockup-light.svg']);

const b = await chromium.launch({ channel: 'chrome' });
for (const o of out) {
  const p = await b.newPage({ viewport: { width: o.w, height: o.h }, deviceScaleFactor: 1 });
  await p.setContent(`<html><body style="margin:0;background:transparent">${o.svg.replace(/width="\d+" height="\d+"/, `width="${o.w}" height="${o.h}"`)}</body></html>`);
  for (const f of o.files) await p.screenshot({ path: path.join(ROOT, f), omitBackground: o.transparent, clip: { x: 0, y: 0, width: o.w, height: o.h } });
  await p.close();
}
await b.close();
for (const app of ['web', 'admin', 'space']) {
  const d = path.join(ROOT, `apps/${app}/app/assets/favicon`);
  execFileSync('python3', ['-c', `from PIL import Image;import os;d='${d}';i=Image.open(d+'/favicon-48.tmp.png');i.save(d+'/favicon.ico',sizes=[(16,16),(32,32),(48,48)]);os.remove(d+'/favicon-48.tmp.png')`]);
}
console.log('assets written:', out.reduce((n, o) => n + o.files.length, 0), 'png + svg + 3 ico');
