import {
  CapsuleGeometry,
  CatmullRomCurve3,
  CylinderGeometry,
  DoubleSide,
  ExtrudeGeometry,
  Group,
  Mesh,
  MeshPhysicalMaterial,
  PlaneGeometry,
  Shape,
  SphereGeometry,
  TorusGeometry,
  TubeGeometry,
  Vector3,
} from "three";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";

// The certificate from web/public/art/certificate.webp, rebuilt from primitives so it can move in 3D:
// a cream page with two rolled corners, a royal folder behind it, two text bars, three dots, a pink
// seal with a check, and two chained cubes (the registry). Colours are the DESIGN.md tokens.
const PAPER = "#ede5d8";
const ROYAL = "#2453d6";
const ROYAL_DARK = "#10266b";
const SEAL = "#f7a8c4";
const SEAL_DARK = "#ee93b3";
const INK = "#0e1a3b";
const LINK = "#a9bdf2";

function clay(color: string, extra: Partial<ConstructorParameters<typeof MeshPhysicalMaterial>[0]> = {}) {
  return new MeshPhysicalMaterial({ color, roughness: 0.55, metalness: 0, clearcoat: 0.25, clearcoatRoughness: 0.5, ...extra });
}

function mesh(geometry: ConstructorParameters<typeof Mesh>[0], material: MeshPhysicalMaterial) {
  const m = new Mesh(geometry, material);
  m.castShadow = true;
  m.receiveShadow = true;
  return m;
}

/** Rolls the part of a flat page beyond a fold line around a cylinder, toward the viewer: the corner
 * curls the way paper does. `n` is the unit direction from the page into the corner. */
function curlCorner(page: PlaneGeometry, cx: number, cy: number, nx: number, ny: number, reach: number, radius: number) {
  const pos = page.attributes.position;
  const fold = cx * nx + cy * ny - reach; // distance of the fold line along n
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i);
    const y = pos.getY(i);
    const s = x * nx + y * ny - fold; // how far past the fold this vertex lies
    if (s <= 0) continue;
    const angle = s / radius;
    const along = radius * Math.sin(angle);
    pos.setXYZ(i, x + (along - s) * nx, y + (along - s) * ny, pos.getZ(i) + radius * (1 - Math.cos(angle)));
  }
}

function folderShape(w: number, h: number) {
  const x = w / 2;
  const y = h / 2;
  const s = new Shape();
  s.moveTo(-x, -y + 0.1);
  s.lineTo(-x, y - 0.1);
  s.quadraticCurveTo(-x, y, -x + 0.1, y);
  s.lineTo(x - 0.62, y);
  s.lineTo(x - 0.45, y - 0.16);
  s.lineTo(x - 0.1, y - 0.16);
  s.quadraticCurveTo(x, y - 0.16, x, y - 0.26);
  s.lineTo(x, -y + 0.1);
  s.quadraticCurveTo(x, -y, x - 0.1, -y);
  s.lineTo(-x + 0.1, -y);
  s.quadraticCurveTo(-x, -y, -x, -y + 0.1);
  return s;
}

/** A scalloped badge outline: `bumps` rounded teeth around a circle. */
function sealShape(radius: number, bumps: number, depth: number) {
  const s = new Shape();
  const steps = bumps * 12;
  for (let i = 0; i <= steps; i++) {
    const t = (i / steps) * Math.PI * 2;
    const r = radius + depth * Math.cos(bumps * t);
    const px = r * Math.cos(t);
    const py = r * Math.sin(t);
    if (i === 0) s.moveTo(px, py);
    else s.lineTo(px, py);
  }
  return s;
}

export function createCertificateModel() {
  const root = new Group();
  root.name = "certificate";

  const paper = clay(PAPER, { roughness: 0.7, clearcoat: 0.1, side: DoubleSide });
  const royal = clay(ROYAL);
  const royalDark = clay(ROYAL_DARK, { roughness: 0.45 });
  const seal = clay(SEAL, { roughness: 0.6 });
  const sealDark = clay(SEAL_DARK, { roughness: 0.6 });
  const ink = clay(INK, { roughness: 0.4 });
  const link = clay(LINK, { metalness: 0.2, roughness: 0.35 });

  // Folder behind the page, peeking out on the right.
  const folder = mesh(
    new ExtrudeGeometry(folderShape(1.55, 2.25), { depth: 0.07, bevelEnabled: true, bevelSize: 0.03, bevelThickness: 0.03, bevelSegments: 3 }),
    royal,
  );
  folder.position.set(0.5, 0.06, -0.2);
  folder.rotation.z = -0.05;
  root.add(folder);

  // The page: a finely divided sheet, gently waved, with its top-right and bottom-left corners rolled.
  const W = 2;
  const H = 2.4;
  const sheet = new PlaneGeometry(W, H, 80, 96);
  const pos = sheet.attributes.position;
  for (let i = 0; i < pos.count; i++) pos.setZ(i, 0.025 * Math.sin(pos.getX(i) * 1.4 + 0.6));
  const d = Math.SQRT1_2;
  curlCorner(sheet, W / 2, H / 2, d, d, 0.5, 0.13);
  curlCorner(sheet, -W / 2, -H / 2, -d, -d, 0.42, 0.11);
  sheet.computeVertexNormals();
  const page = mesh(sheet, paper);
  root.add(page);

  // Two text bars and three dots, raised off the page.
  const bar = new CapsuleGeometry(0.075, 1.05, 8, 16);
  [0.62, 0.3].forEach((y) => {
    const b = mesh(bar, royalDark);
    b.rotation.z = Math.PI / 2;
    b.position.set(-0.22, y, 0.11); // clear of the page's wave
    root.add(b);
  });
  const dot = new CylinderGeometry(0.1, 0.1, 0.06, 32);
  [-0.68, -0.38, -0.08].forEach((x) => {
    const d = mesh(dot, royal);
    d.rotation.x = Math.PI / 2;
    d.position.set(x, -0.08, 0.08);
    root.add(d);
  });

  // The seal: a scalloped pink disc, an inner ring, and a navy check.
  const sealGroup = new Group();
  const disc = mesh(
    new ExtrudeGeometry(sealShape(0.5, 18, 0.035), { depth: 0.09, bevelEnabled: true, bevelSize: 0.025, bevelThickness: 0.03, bevelSegments: 4 }),
    seal,
  );
  sealGroup.add(disc);
  const ring = mesh(new TorusGeometry(0.37, 0.022, 12, 64), sealDark);
  ring.position.z = 0.125;
  sealGroup.add(ring);
  const checkPath = new CatmullRomCurve3(
    [new Vector3(-0.17, 0.0, 0), new Vector3(-0.05, -0.12, 0), new Vector3(0.19, 0.15, 0)],
    false,
    "catmullrom",
    0,
  );
  const check = mesh(new TubeGeometry(checkPath, 32, 0.055, 12, false), ink);
  check.position.z = 0.15;
  sealGroup.add(check);
  [checkPath.getPoint(0), checkPath.getPoint(1)].forEach((p) => {
    const cap = mesh(new SphereGeometry(0.055, 16, 12), ink); // round ends on the check
    cap.position.set(p.x, p.y, 0.15);
    sealGroup.add(cap);
  });
  sealGroup.position.set(0.66, -0.74, 0.1);
  sealGroup.rotation.set(0.05, -0.12, 0.08);
  root.add(sealGroup);

  // Two chained cubes on the lower left: the registry.
  const cube = new RoundedBoxGeometry(0.34, 0.34, 0.34, 4, 0.05);
  const left = mesh(cube, royal);
  left.position.set(-1.18, -0.38, 0.14);
  left.rotation.set(0.35, 0.5, 0.1);
  root.add(left);
  const right = mesh(cube, royal);
  right.position.set(-0.98, -0.82, 0.3);
  right.rotation.set(0.25, 0.4, -0.15);
  root.add(right);
  const chain = mesh(new CylinderGeometry(0.03, 0.03, 0.42, 12), link);
  chain.position.copy(left.position).lerp(right.position, 0.5);
  chain.lookAt(right.position);
  chain.rotateX(Math.PI / 2);
  root.add(chain);

  return root;
}
