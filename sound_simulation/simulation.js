const canvas = document.getElementById('simCanvas');
const ctx = canvas.getContext('2d');

const WIDTH = canvas.width;
const HEIGHT = canvas.height;

// Ear point
let ear = {x: WIDTH * 0.75, y: HEIGHT * 0.5, r: 16};
let isDraggingEar = false;

// Sound pulse
let sound = null;
const speed = 3.5;

// Walls (rectangle)
const walls = [
  // top
  {x1: 0, y1: 0, x2: WIDTH, y2: 0},
  // right
  {x1: WIDTH, y1: 0, x2: WIDTH, y2: HEIGHT},
  // bottom
  {x1: WIDTH, y1: HEIGHT, x2: 0, y2: HEIGHT},
  // left
  {x1: 0, y1: HEIGHT, x2: 0, y2: 0},
];

// Utility: distance from point to point
function dist(a, b) {
  return Math.sqrt((a.x-b.x)*(a.x-b.x) + (a.y-b.y)*(a.y-b.y));
}

// Utility: play beep if sound reaches ear
function playBeep() {
  if (!window.AudioContext) return;
  try {
    const ctx = new AudioContext();
    const o = ctx.createOscillator();
    o.type = "sine";
    o.frequency.value = 700;
    o.connect(ctx.destination);
    o.start();
    o.stop(ctx.currentTime + 0.12);
    setTimeout(() => ctx.close(), 150);
  } catch {}
}

// Find intersection of line segment and walls, returns {point, wall, t} or null
function wallIntersect(x, y, dx, dy) {
  let minT = Infinity, hit = null, hitWall = null;
  for (let wall of walls) {
    const den = (wall.x1 - wall.x2) * dy - (wall.y1 - wall.y2) * dx;
    if (den === 0) continue; // parallel
    const t = ((wall.x1 - x) * dy - (wall.y1 - y) * dx) / den;
    const u = -((wall.x1 - wall.x2) * (wall.y1 - y) - (wall.y1 - wall.y2) * (wall.x1 - x)) / den;
    if (t >= 0 && t <= 1 && u > 0 && u < minT) {
      minT = u;
      hit = {x: x + dx * u, y: y + dy * u};
      hitWall = wall;
    }
  }
  return hit ? {point: hit, wall: hitWall, t: minT} : null;
}

// Animate sound pulse (with bounces)
function update() {
  ctx.clearRect(0, 0, WIDTH, HEIGHT);

  // Draw walls
  ctx.strokeStyle = "#444";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(walls[0].x1, walls[0].y1);
  for (let w of walls) ctx.lineTo(w.x2, w.y2);
  ctx.stroke();

  // Draw ear
  ctx.beginPath();
  ctx.arc(ear.x, ear.y, ear.r, 0, 2 * Math.PI);
  ctx.fillStyle = "#36a2eb";
  ctx.fill();
  ctx.strokeStyle = "#1565c0";
  ctx.stroke();

  // Draw sound pulse
  if (sound) {
    ctx.save();
    ctx.strokeStyle = "#d32f2f";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(sound.path[0].x, sound.path[0].y);
    for (let p of sound.path) ctx.lineTo(p.x, p.y);
    ctx.stroke();
    ctx.restore();

    // Propagate
    let {x, y, dx, dy, bounces, path} = sound;
    let t = 1.0;
    let moveX = dx * speed, moveY = dy * speed;
    // Check for wall collision
    let hit = wallIntersect(x, y, moveX, moveY);
    if (hit) {
      // Collide with wall: reflect direction
      let nx = hit.wall.y2 - hit.wall.y1;
      let ny = hit.wall.x1 - hit.wall.x2;
      const len = Math.sqrt(nx*nx + ny*ny);
      nx /= len; ny /= len;
      // reflect (dx, dy)
      let dot = dx*nx + dy*ny;
      dx = dx - 2*dot*nx;
      dy = dy - 2*dot*ny;
      // Move to hit point, add to path
      x = hit.point.x;
      y = hit.point.y;
      path.push({x, y});
      bounces += 1;
      if (bounces > 8) sound = null; // Max bounces
      else sound = {x, y, dx, dy, bounces, path};
    } else {
      // Move forward
      x += moveX;
      y += moveY;
      path.push({x, y});
      sound = {x, y, dx, dy, bounces, path};
    }

    // Check for intersection with ear
    if (dist(sound, ear) < ear.r) {
      // Draw effect
      ctx.save();
      ctx.beginPath();
      ctx.arc(ear.x, ear.y, ear.r+8, 0, 2*Math.PI);
      ctx.strokeStyle = "#ffeb3b";
      ctx.lineWidth = 4;
      ctx.stroke();
      ctx.restore();
      playBeep();
      sound = null; // End sound
    }
  }

  requestAnimationFrame(update);
}
requestAnimationFrame(update);

// User interaction: tap/click to emit sound, drag ear
function getMousePos(evt) {
  let rect = canvas.getBoundingClientRect();
  let x, y;
  if (evt.touches) {
    x = evt.touches[0].clientX - rect.left;
    y = evt.touches[0].clientY - rect.top;
  } else {
    x = evt.clientX - rect.left;
    y = evt.clientY - rect.top;
  }
  return {x, y};
}

canvas.addEventListener('mousedown', startInteraction);
canvas.addEventListener('touchstart', startInteraction);

function startInteraction(evt) {
  const pos = getMousePos(evt);
  if (dist(pos, ear) < ear.r + 6) {
    isDraggingEar = true;
    evt.preventDefault();
    return;
  }
  // Emit sound from clicked position, toward touch/click direction
  let angle = Math.atan2(ear.y - pos.y, ear.x - pos.x);
  sound = {
    x: pos.x, y: pos.y,
    dx: Math.cos(angle), dy: Math.sin(angle),
    bounces: 0,
    path: [{x: pos.x, y: pos.y}]
  };
}

canvas.addEventListener('mousemove', moveInteraction);
canvas.addEventListener('touchmove', moveInteraction);

function moveInteraction(evt) {
  if (!isDraggingEar) return;
  const pos = getMousePos(evt);
  ear.x = Math.max(ear.r, Math.min(WIDTH - ear.r, pos.x));
  ear.y = Math.max(ear.r, Math.min(HEIGHT - ear.r, pos.y));
  evt.preventDefault();
}

canvas.addEventListener('mouseup', endInteraction);
canvas.addEventListener('touchend', endInteraction);

function endInteraction(evt) {
  isDraggingEar = false;
}