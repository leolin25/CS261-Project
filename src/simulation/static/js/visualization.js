import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

const container = document.getElementById('scene-root');

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x020202);
scene.fog = new THREE.Fog(0x020202, 120, 260);

const camera = new THREE.PerspectiveCamera(55, container.clientWidth / container.clientHeight, 0.1, 1000);
camera.position.set(34, 24, 36);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(container.clientWidth, container.clientHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
container.appendChild(renderer.domElement);

const labelRenderer = new CSS2DRenderer();
labelRenderer.setSize(container.clientWidth, container.clientHeight);
labelRenderer.domElement.style.position = 'absolute';
labelRenderer.domElement.style.top = '0';
labelRenderer.domElement.style.left = '0';
labelRenderer.domElement.style.pointerEvents = 'none';
container.appendChild(labelRenderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.maxPolarAngle = Math.PI / 2.08;
controls.minDistance = 16;
controls.maxDistance = 120;
controls.target.set(0, 0, 0);

const ambient = new THREE.AmbientLight(0xffffff, 0.9);
scene.add(ambient);

const keyLight = new THREE.DirectionalLight(0xa5d8ff, 2.5);
keyLight.position.set(20, 28, 10);
keyLight.castShadow = true;
scene.add(keyLight);

const rimLight = new THREE.DirectionalLight(0x7c3aed, 1.6);
rimLight.position.set(-24, 16, -18);
scene.add(rimLight);

const ground = new THREE.Mesh(
  new THREE.CircleGeometry(95, 100),
  new THREE.MeshStandardMaterial({ color: 0x07111f, metalness: 0.15, roughness: 0.92 })
);
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
scene.add(ground);

const grid = new THREE.GridHelper(180, 50, 0x19324f, 0x0b1626);
grid.position.y = 0.02;
scene.add(grid);

function createRunway(x, z, length, width, rotation = 0) {
  const runwayGroup = new THREE.Group();

  const runway = new THREE.Mesh(
    new THREE.BoxGeometry(width, 0.25, length),
    new THREE.MeshStandardMaterial({ color: 0x23262d, roughness: 0.85, metalness: 0.12 })
  );
  runway.receiveShadow = true;
  runway.castShadow = true;
  runwayGroup.add(runway);

  const centerLine = new THREE.Mesh(
    new THREE.BoxGeometry(0.28, 0.02, length * 0.85),
    new THREE.MeshBasicMaterial({ color: 0xf8fafc })
  );
  centerLine.position.y = 0.14;
  runwayGroup.add(centerLine);

  const edgeGlow = new THREE.Mesh(
    new THREE.BoxGeometry(width + 0.2, 0.02, length + 0.2),
    new THREE.MeshBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.15 })
  );
  edgeGlow.position.y = 0.15;
  runwayGroup.add(edgeGlow);

  runwayGroup.position.set(x, 0.12, z);
  runwayGroup.rotation.y = rotation;
  scene.add(runwayGroup);
}

function createTerminal() {
  const terminal = new THREE.Group();

  const base = new THREE.Mesh(
    new THREE.BoxGeometry(18, 3.5, 9),
    new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.3, roughness: 0.45 })
  );
  base.castShadow = true;
  base.receiveShadow = true;
  terminal.add(base);

  const tower = new THREE.Mesh(
    new THREE.CylinderGeometry(1.4, 2.4, 10, 8),
    new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.28, roughness: 0.35 })
  );
  tower.position.set(8, 6.2, -1);
  tower.castShadow = true;
  terminal.add(tower);

  const glass = new THREE.Mesh(
    new THREE.BoxGeometry(18.4, 0.2, 9.4),
    new THREE.MeshStandardMaterial({ color: 0x7dd3fc, emissive: 0x164e63, transparent: true, opacity: 0.24 })
  );
  glass.position.y = 1.2;
  terminal.add(glass);

  terminal.position.set(-22, 1.8, 2);
  scene.add(terminal);
}

function createTaxiLines() {
  const material = new THREE.MeshBasicMaterial({ color: 0xf59e0b });
  const strips = [
    { x: -8, z: 0, w: 0.18, l: 20, r: Math.PI / 2 },
    { x: -12, z: 10, w: 0.18, l: 26, r: 0 },
    { x: 0, z: -12, w: 0.18, l: 28, r: Math.PI / 2 },
  ];

  strips.forEach(({ x, z, w, l, r }) => {
    const strip = new THREE.Mesh(new THREE.BoxGeometry(w, 0.03, l), material);
    strip.position.set(x, 0.14, z);
    strip.rotation.y = r;
    scene.add(strip);
  });
}

function createHoldingRing() {
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(18, 0.08, 10, 100),
    new THREE.MeshBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.45 })
  );
  ring.rotation.x = Math.PI / 2;
  ring.position.set(16, 11, -12);
  scene.add(ring);
}

createRunway(8, 0, 58, 6, 0);
createRunway(8, -18, 48, 5.2, 0.22);
createTerminal();
createTaxiLines();
createHoldingRing();

const aircraftConfigs = [
  { name: 'AR-101', color: 0x38bdf8, base: new THREE.Vector3(-6, 2.4, 10), mode: 'taxi' },
  { name: 'AR-204', color: 0xf59e0b, base: new THREE.Vector3(0, 2.8, -8), mode: 'taxi' },
  { name: 'AR-309', color: 0xef4444, base: new THREE.Vector3(10, 7.2, 12), mode: 'approach' },
  { name: 'AR-417', color: 0x22c55e, base: new THREE.Vector3(18, 10.8, -12), mode: 'hold' },
  { name: 'AR-520', color: 0xa855f7, base: new THREE.Vector3(25, 11.4, -12), mode: 'hold' },
  { name: 'AR-632', color: 0xf97316, base: new THREE.Vector3(13, 6.4, 18), mode: 'approach' },
];

function createAircraft({ name, color, base, mode }) {
  const group = new THREE.Group();

  const bodyMaterial = new THREE.MeshStandardMaterial({
    color,
    metalness: 0.35,
    roughness: 0.45,
  });

  const wingMaterial = new THREE.MeshStandardMaterial({
    color: 0xdfe7ef,
    metalness: 0.2,
    roughness: 0.6,
  });

  const darkMaterial = new THREE.MeshStandardMaterial({
    color: 0x1a2233,
    metalness: 0.15,
    roughness: 0.75,
  });

  const engineMaterial = new THREE.MeshStandardMaterial({
    color: 0x9aa6b2,
    metalness: 0.5,
    roughness: 0.4,
  });

  const noseMaterial = new THREE.MeshStandardMaterial({
    color: 0xf8fbff,
    metalness: 0.15,
    roughness: 0.55,
  });

  const body = new THREE.Mesh(
    new THREE.CapsuleGeometry(0.18, 1.25, 8, 16),
    bodyMaterial
  );
  body.rotation.z = Math.PI / 2;
  group.add(body);

  const nose = new THREE.Mesh(
    new THREE.SphereGeometry(0.16, 16, 16),
    noseMaterial
  );
  nose.position.x = 0.82;
  nose.scale.set(1.2, 0.92, 0.92);
  group.add(nose);

  const cockpit = new THREE.Mesh(
    new THREE.SphereGeometry(0.09, 12, 12),
    darkMaterial
  );
  cockpit.position.set(0.62, 0.08, 0);
  cockpit.scale.set(1.35, 0.75, 0.7);
  group.add(cockpit);

  const mainWing = new THREE.Mesh(
    new THREE.BoxGeometry(0.18, 0.03, 1.45),
    wingMaterial
  );
  mainWing.position.set(-0.02, 0.01, 0);
  mainWing.rotation.x = 0.03;
  mainWing.rotation.z = -0.08;
  group.add(mainWing);

  const wingTipLeft = new THREE.Mesh(
    new THREE.BoxGeometry(0.08, 0.16, 0.03),
    wingMaterial
  );
  wingTipLeft.position.set(0.02, 0.08, 0.72);
  wingTipLeft.rotation.x = -0.35;
  group.add(wingTipLeft);

  const wingTipRight = wingTipLeft.clone();
  wingTipRight.position.z = -0.72;
  wingTipRight.rotation.x = 0.35;
  group.add(wingTipRight);

  const tailWing = new THREE.Mesh(
    new THREE.BoxGeometry(0.14, 0.025, 0.65),
    wingMaterial
  );
  tailWing.position.set(-0.68, 0.12, 0);
  group.add(tailWing);

  const fin = new THREE.Mesh(
    new THREE.BoxGeometry(0.22, 0.28, 0.035),
    wingMaterial
  );
  fin.position.set(-0.7, 0.2, 0);
  fin.rotation.z = -0.1;
  group.add(fin);

  const engineLeft = new THREE.Mesh(
    new THREE.CylinderGeometry(0.07, 0.055, 0.24, 16),
    engineMaterial
  );
  engineLeft.rotation.z = Math.PI / 2;
  engineLeft.position.set(-0.02, -0.09, 0.36);
  group.add(engineLeft);

  const engineRight = engineLeft.clone();
  engineRight.position.z = -0.36;
  group.add(engineRight);

  const engineIntakeLeft = new THREE.Mesh(
    new THREE.CylinderGeometry(0.05, 0.05, 0.02, 16),
    darkMaterial
  );
  engineIntakeLeft.rotation.z = Math.PI / 2;
  engineIntakeLeft.position.set(0.1, -0.09, 0.36);
  group.add(engineIntakeLeft);

  const engineIntakeRight = engineIntakeLeft.clone();
  engineIntakeRight.position.z = -0.36;
  group.add(engineIntakeRight);

  const labelEl = document.createElement('div');
  labelEl.className = 'aircraft-label';
  labelEl.textContent = name;
  const label = new CSS2DObject(labelEl);
  label.position.set(0, 0.55, 0);
  group.add(label);

  group.position.copy(base);
  group.userData = {
    mode,
    base: base.clone(),
    speed: 0.3 + Math.random() * 0.35,
    phase: Math.random() * Math.PI * 2
  };

  group.traverse((child) => {
    if (child.isMesh) {
      child.castShadow = true;
      child.receiveShadow = true;
    }
  });
  group.scale.set(2.4, 2.4, 2.4);
  scene.add(group);
  return group;
}

const aircraft = aircraftConfigs.map(createAircraft);

const pulseMaterial = new THREE.MeshBasicMaterial({ color: 0x7dd3fc, transparent: true, opacity: 0.12 });
for (let i = 0; i < 12; i += 1) {
  const light = new THREE.Mesh(new THREE.SphereGeometry(0.12, 10, 10), pulseMaterial);
  light.position.set(-18 + i * 4.2, 0.35, 14);
  scene.add(light);
}

const clock = new THREE.Clock();

function animateAircraft(elapsed) {
  aircraft.forEach((plane, index) => {
    const { mode, base, speed, phase } = plane.userData;

    if (mode === 'hold') {
      const angle = elapsed * speed + phase;
      const radius = 8 + index;
      plane.position.set(16 + Math.cos(angle) * radius, 10 + (index % 2) * 1.3, -12 + Math.sin(angle) * radius);
      plane.rotation.y = -angle + Math.PI / 2;
      plane.rotation.z = Math.sin(angle * 2) * 0.08;
    } else if (mode === 'approach') {
      plane.position.x = base.x - ((elapsed * (2.8 + index * 0.2)) % 28);
      plane.position.y = Math.max(1.8, base.y - ((elapsed * 0.42) % 5));
      plane.position.z = base.z + Math.sin(elapsed * speed + phase) * 1.5;
      plane.rotation.y = Math.PI;
      plane.rotation.z = -0.05;
    } else {
      plane.position.x = base.x + Math.sin(elapsed * speed + phase) * 5.5;
      plane.position.z = base.z + Math.cos(elapsed * speed + phase) * 1.3;
      plane.position.y = base.y;
      plane.rotation.y = -Math.PI / 2 + Math.sin(elapsed * speed + phase) * 0.08;
      plane.rotation.z = 0;
    }
  });
}

function animate() {
  requestAnimationFrame(animate);
  const elapsed = clock.getElapsedTime();
  animateAircraft(elapsed);
  controls.update();
  renderer.render(scene, camera);
  labelRenderer.render(scene, camera);
}

animate();

function onResize() {
  camera.aspect = container.clientWidth / container.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(container.clientWidth, container.clientHeight);
  labelRenderer.setSize(container.clientWidth, container.clientHeight);
}

window.addEventListener('resize', onResize);
