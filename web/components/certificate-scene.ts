import {
  AmbientLight,
  DirectionalLight,
  Group,
  HemisphereLight,
  MathUtils,
  Mesh,
  NeutralToneMapping,
  PCFShadowMap,
  PerspectiveCamera,
  PMREMGenerator,
  Scene,
  SpotLight,
  SRGBColorSpace,
  WebGLRenderer,
} from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { createCertificateModel } from "./certificate-model";

/** Pose at a moment: a slow float up and down with a gentle sway, nudged by the pointer. */
export function certificatePose(seconds: number, pointerX: number, pointerY: number, still: boolean) {
  if (still) return { yaw: -0.3, pitch: 0.08, roll: 0.04, lift: 0 };
  return {
    yaw: -0.3 + Math.sin(seconds * 0.55) * 0.2 + pointerX * 0.18,
    pitch: 0.08 + Math.sin(seconds * 0.8) * 0.04 - pointerY * 0.12,
    roll: 0.04 + Math.sin(seconds * 0.45) * 0.03,
    lift: Math.sin(seconds * 1.1) * 0.12,
  };
}

function dispose(group: Group) {
  group.traverse((object) => {
    if (object instanceof Mesh) {
      object.geometry.dispose();
      const materials = Array.isArray(object.material) ? object.material : [object.material];
      materials.forEach((material) => material.dispose());
    }
  });
}

/** Renders the certificate into `host` and calls `onReady` after the first frame. Throws when WebGL
 * is unavailable, so the caller keeps its static image. Returns a cleanup function. */
export function mountCertificate(host: HTMLElement, onReady: () => void): () => void {
  const renderer = new WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
  renderer.outputColorSpace = SRGBColorSpace;
  // Neutral keeps the royal and pink of the art saturated; ACES washed them toward pastel.
  renderer.toneMapping = NeutralToneMapping;
  renderer.toneMappingExposure = 1;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = PCFShadowMap;
  renderer.setClearColor(0x000000, 0);
  renderer.domElement.setAttribute("aria-hidden", "true");
  renderer.domElement.className = "cert3d__canvas";
  host.appendChild(renderer.domElement);

  const scene = new Scene();
  const pmrem = new PMREMGenerator(renderer);
  const environment = pmrem.fromScene(new RoomEnvironment()).texture;
  scene.environment = environment;
  scene.environmentIntensity = 0.45; // a soft studio sheen, not a white wash
  pmrem.dispose();

  const camera = new PerspectiveCamera(30, 1, 0.1, 100);
  camera.position.set(0, 0, 7.4);

  const model = createCertificateModel();
  const rig = new Group();
  rig.add(model);
  scene.add(rig);

  scene.add(new HemisphereLight("#eef2fd", "#10266b", 0.7));
  scene.add(new AmbientLight("#c9d5f5", 0.25));
  const key = new SpotLight("#ffffff", 60, 20, Math.PI / 5, 0.5, 1.3);
  key.position.set(-3.5, 4.5, 6);
  key.castShadow = true; // the parts shade each other; the page's CSS drop-shadow grounds the whole
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.focus = 0.45; // fit the shadow map to the object, not the whole cone
  key.shadow.radius = 3;
  key.shadow.bias = -0.0005;
  key.shadow.normalBias = 0.02; // no shadow acne on the folder's bevel
  scene.add(key);
  const rim = new DirectionalLight("#9fb6ff", 1.1);
  rim.position.set(4, 1.5, -2);
  scene.add(rim);

  let ready = false;
  const resize = () => {
    const width = Math.max(host.clientWidth, 1);
    const height = Math.max(host.clientHeight, 1);
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    if (ready) renderer.render(scene, camera); // setSize clears the canvas, also when motion is reduced
  };
  const resizeObserver = new ResizeObserver(resize);
  resizeObserver.observe(host);
  resize();

  let visible = true;
  const intersectionObserver = new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
  });
  intersectionObserver.observe(host);

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const target = { x: 0, y: 0 };
  const pointer = { x: 0, y: 0 };
  const onPointer = (event: PointerEvent) => {
    target.x = MathUtils.clamp((event.clientX / window.innerWidth - 0.5) * 2, -1, 1);
    target.y = MathUtils.clamp((event.clientY / window.innerHeight - 0.5) * 2, -1, 1);
  };
  window.addEventListener("pointermove", onPointer, { passive: true });

  let frame = 0;
  const render = (time: number) => {
    frame = requestAnimationFrame(render);
    if (!visible || document.hidden) return;
    if (ready && reduceMotion.matches) return; // one still frame is enough
    pointer.x = MathUtils.lerp(pointer.x, target.x, 0.05);
    pointer.y = MathUtils.lerp(pointer.y, target.y, 0.05);
    const pose = certificatePose(time / 1000, pointer.x, pointer.y, reduceMotion.matches);
    rig.rotation.set(pose.pitch, pose.yaw, pose.roll);
    rig.position.y = pose.lift;
    renderer.render(scene, camera);
    if (!ready) {
      ready = true;
      onReady();
    }
  };
  frame = requestAnimationFrame(render);

  return () => {
    cancelAnimationFrame(frame);
    window.removeEventListener("pointermove", onPointer);
    resizeObserver.disconnect();
    intersectionObserver.disconnect();
    dispose(rig);
    environment.dispose();
    renderer.dispose();
    renderer.domElement.remove();
  };
}
