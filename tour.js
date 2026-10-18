// "A look inside". On wide screens the section holds still while it scrolls
// past and steps through the screenshots, the list on the left marking which
// one is up. Each change of screen is a WebGL morph: a soft, ragged front
// rises through the picture, with a little blur and flow around it. Without
// JavaScript or on narrow screens it stays a plain list; without WebGL, or
// with reduced motion, the pictures simply swap.
(function () {
  var tour = document.querySelector("[data-tour]");
  var pin = tour && tour.querySelector(".tour-pin");
  var grid = pin && pin.querySelector(".tour-grid");
  if (!grid) return;
  var steps = Array.prototype.slice.call(tour.querySelectorAll(".tour-step"));
  var imgs = steps.map(function (s) { return s.querySelector("img"); });
  if (steps.length < 2) return;

  var wide = matchMedia("(min-width: 900px)");
  var still = matchMedia("(prefers-reduced-motion: reduce)");
  var DURATION = 1100;

  // The morph shader. Purely a function of the progress uP, from picture A
  // to picture B. The look, in picture heights unless noted:
  var LOOK = {
    SOFT: 0.07, // half-width of the soft edge where one picture becomes the other
    INK: 0.05, // marks (dark or coloured) swap this far ahead of the front
    AMP: 0.07, // how ragged the front is
    BOW: 0.05, // the middle leads, the sides lag
    TILT: 0.05, // each front leans a little, alternating
    ZONE: 0.09, // reach of the blur and the flow around the front
    BLUR: 0.016, // max blur radius, of the width
    FLOW: 0.012, // how far content near the front is carried up
    GROW: 0.04, // the incoming picture starts this much larger...
    DROP: 0.03, // ...and this much lower
    VEIL: 0.1, // light on the front, so the overlap never goes muddy
  };

  var VERT = "attribute vec2 aPos; varying vec2 vUv;" +
    "void main() { vUv = vec2(aPos.x * 0.5 + 0.5, 0.5 - aPos.y * 0.5); gl_Position = vec4(aPos, 0.0, 1.0); }";

  // vUv runs top-down, like the images' rows, so textures need no flip.
  var FRAG = `
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
${Object.keys(LOOK).map(function (k) { return "#define " + k + " " + LOOK[k].toFixed(4); }).join("\n")}
varying vec2 vUv;
uniform sampler2D uA;
uniform sampler2D uB;
uniform float uP;      // 0..1 from A to B
uniform float uSeed;   // which transition, so each front is its own
uniform float uAspect; // canvas width / height

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
             mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

float fbm(vec2 p) {
  float v = 0.0;
  float a = 0.5;
  for (int i = 0; i < 4; i++) {
    v += a * noise(p);
    p = p * 2.03 + 17.0;
    a *= 0.5;
  }
  return v;
}

vec4 tap(sampler2D t, vec2 uv) { return vec4(texture2D(t, uv).rgb, 1.0); }

// A small disc blur on a golden-angle spiral; one tap when r is tiny.
vec4 soft(sampler2D t, vec2 uv, float r) {
  vec4 c = tap(t, uv);
  if (r < 0.0006) return c;
  for (int i = 1; i < 14; i++) {
    float fi = float(i);
    float a = fi * 2.39996;
    c += tap(t, uv + vec2(cos(a), sin(a) * uAspect) * (sqrt(fi / 13.0) * r));
  }
  return c / 14.0;
}

// How much of a mark a pixel is: dark or coloured, against a pale ground.
float ink(vec4 p) {
  float l = dot(p.rgb, vec3(0.299, 0.587, 0.114));
  float s = max(p.r, max(p.g, p.b)) - min(p.r, min(p.g, p.b));
  return clamp((1.0 - l) * 1.4 + s * 0.8, 0.0, 1.0);
}

void main() {
  vec2 uv = vUv;
  if (uP <= 0.0) {
    gl_FragColor = tap(uA, uv);
    return;
  }
  float p = uP;

  // Blur, flow and veil come and go with the move, so both ends are exactly
  // the still pictures.
  float env = smoothstep(0.0, 0.12, p) * (1.0 - smoothstep(0.88, 1.0, p));

  // The front rises from below the picture to above it, ragged, bowed and
  // leaning.
  float x = uv.x - 0.5;
  float lean = TILT * (mod(uSeed, 2.0) * 2.0 - 1.0);
  float lag = SOFT + AMP * 0.5 + abs(lean) * 0.5 + 0.01;
  float edge = mix(1.0 + lag + INK, -lag - BOW, p);
  float rag = fbm(vec2(uv.x * 1.9 + uSeed * 3.1, p * 1.3 + uSeed * 1.7)) - 0.5;
  float front = edge + BOW * 4.0 * x * x + lean * x + rag * AMP;
  float d = uv.y - front; // > 0: the front has passed, B shows

  float near = exp(-(d * d) / (ZONE * ZONE)) * env;

  // Both pictures are carried up by the front together; the incoming one
  // settles from a touch larger and lower, the outgoing one eases back a hair.
  vec2 flow = vec2(0.0, FLOW * near);
  vec2 o = vec2(0.5, 0.32);
  float q = p * p * (3.0 - 2.0 * p);
  vec2 uvA = (uv - o) / (1.0 - 0.006 * q) + o + flow;
  float settle = smoothstep(0.0, 0.85, p);
  vec2 uvB = (uv - o) / mix(1.0 + GROW, 1.0, settle) + o - vec2(0.0, DROP) * (1.0 - settle) + flow;

  float r = BLUR * near;
  vec4 a = soft(uA, uvA, r);
  vec4 b = soft(uB, uvB, r);

  // Marks swap a little ahead of the ground, so elements change shape rather
  // than being cut by a line. Read off softened copies, only near the front.
  float marks = 0.0;
  if (d > -(SOFT + INK + 0.02) && d < SOFT + 0.02) {
    marks = max(ink(soft(uA, uvA, 0.012)), ink(soft(uB, uvB, 0.012)));
  }
  float mask = smoothstep(-SOFT, SOFT, d + INK * marks);
  vec4 c = mix(a, b, mask);

  // Light where the two overlap most, instead of a muddy mix.
  c.rgb = mix(c.rgb, vec3(1.0), VEIL * env * (1.0 - abs(mask * 2.0 - 1.0)));
  gl_FragColor = c;
}`;

  var canvas = null;
  var gl = null;
  var u = null;
  var tex = [];
  var failed = false;

  function compile(type, source) {
    var shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (gl.getShaderParameter(shader, gl.COMPILE_STATUS)) return shader;
    if (!gl.isContextLost()) console.warn("tour.js:", gl.getShaderInfoLog(shader));
    return null;
  }

  function start() {
    if (gl || failed) return !!gl;
    gl = canvas.getContext("webgl", { alpha: false, antialias: false, depth: false, stencil: false, powerPreference: "low-power" });
    var vs = gl && compile(gl.VERTEX_SHADER, VERT);
    var fs = gl && compile(gl.FRAGMENT_SHADER, FRAG);
    var program = gl && gl.createProgram();
    if (!vs || !fs || !program) return fail();
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return fail();
    gl.useProgram(program);

    // One triangle that covers the viewport.
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    var pos = gl.getAttribLocation(program, "aPos");
    gl.enableVertexAttribArray(pos);
    gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0);

    u = {};
    ["uA", "uB", "uP", "uSeed", "uAspect"].forEach(function (name) { u[name] = gl.getUniformLocation(program, name); });
    gl.uniform1i(u.uA, 0);
    gl.uniform1i(u.uB, 1);
    return true;
  }

  function fail() {
    gl = null;
    failed = true;
    return false;
  }

  function texture(i) {
    var img = imgs[i];
    if (tex[i] || !img.complete || !img.naturalWidth) return tex[i];
    var t = gl.createTexture();
    gl.activeTexture(gl.TEXTURE2);
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, img);
    return (tex[i] = t);
  }

  function draw(a, b, p, seed) {
    if (!start() || gl.isContextLost()) return false;
    var dpr = Math.min(2, devicePixelRatio || 1);
    var w = Math.max(1, Math.round(canvas.clientWidth * dpr));
    var h = Math.max(1, Math.round(canvas.clientHeight * dpr));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
      gl.viewport(0, 0, w, h);
    }
    var ta = texture(a);
    var tb = texture(b);
    if (!ta || !tb) return false;
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, ta);
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, tb);
    gl.uniform1f(u.uP, p);
    gl.uniform1f(u.uSeed, seed);
    gl.uniform1f(u.uAspect, w / h);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    return true;
  }

  // Which step is up (the text) and which picture shows (it trails the text
  // by one morph).
  var current = 0;
  var shown = 0;
  var target = 0;
  var raf = 0;
  var seed = 0;

  // Behind the picture, a blurred copy of each screenshot: the light of the
  // screen, crossfading to the next one while the morph runs.
  var glows = [];

  function mark(i) {
    current = i;
    steps.forEach(function (s, k) { s.classList.toggle("on", k === i); });
    glows.forEach(function (g, k) { g.classList.toggle("on", k === i); });
  }

  function picture(i) {
    shown = i;
    steps.forEach(function (s, k) { s.classList.toggle("shown", k === i); });
  }

  function morph(to) {
    if (raf) {
      cancelAnimationFrame(raf);
      raf = 0;
      picture(target);
    }
    var from = shown;
    target = to;
    seed = (seed + 1) % 8;
    if (from === to || still.matches || !draw(from, to, 0.0001, seed)) {
      canvas.classList.remove("on");
      return picture(to);
    }
    canvas.classList.add("on");
    var t0 = performance.now();
    var frame = function (now) {
      var t = Math.min(1, (now - t0) / DURATION);
      draw(from, to, t < 0.5 ? 2 * t * t : 1 - Math.pow(2 - 2 * t, 2) / 2, seed);
      if (t < 1) return (raf = requestAnimationFrame(frame));
      raf = 0;
      // the canvas ends on B exactly: swap the pictures under it at once, no crossfade
      tour.classList.add("snap");
      picture(to);
      canvas.classList.remove("on");
      requestAnimationFrame(function () { tour.classList.remove("snap"); });
    };
    raf = requestAnimationFrame(frame);
  }

  // Where in the section the page is: 0 as it pins, 1 as it lets go.
  function along() {
    var span = tour.offsetHeight - pin.offsetHeight;
    var top = parseFloat(getComputedStyle(pin).top) || 0;
    return { span: span, top: top, p: span > 0 ? (top - tour.getBoundingClientRect().top) / span : 0 };
  }

  var ticking = false;
  function update() {
    ticking = false;
    var i = Math.floor(Math.min(Math.max(along().p, 0), 0.9999) * steps.length);
    if (i !== current) {
      mark(i);
      morph(i);
    }
  }
  function onScroll() {
    if (!ticking) requestAnimationFrame(update);
    ticking = true;
  }

  // A click on a step scrolls to it.
  steps.forEach(function (s, k) {
    s.querySelector(".tour-text").addEventListener("click", function () {
      if (!tour.classList.contains("is-live")) return;
      var a = along();
      var y = tour.getBoundingClientRect().top + scrollY - a.top + (a.span * (k + 0.15)) / steps.length;
      scrollTo({ top: y, behavior: still.matches ? "auto" : "smooth" });
    });
  });

  // The steps and the picture rise in the first time the section comes into view.
  function reveal() {
    if (still.matches || !("IntersectionObserver" in window) || tour.getBoundingClientRect().top < innerHeight * 0.8) {
      return tour.classList.add("seen");
    }
    var seen = new IntersectionObserver(function (entries) {
      if (!entries[0].isIntersecting) return;
      tour.classList.add("seen");
      seen.disconnect();
    }, { rootMargin: "0px 0px -20% 0px" });
    seen.observe(tour);
  }

  function live(on) {
    tour.classList.toggle("is-live", on);
    // live, row 1 is the room above the list (see styles.css)
    steps.forEach(function (s, k) { s.querySelector(".tour-text").style.gridRow = on ? String(k + 2) : ""; });
    if (!on) return removeEventListener("scroll", onScroll);
    if (!canvas) {
      canvas = document.createElement("canvas");
      canvas.className = "tour-canvas";
      canvas.setAttribute("aria-hidden", "true");
      canvas.style.aspectRatio = imgs[0].getAttribute("width") + " / " + imgs[0].getAttribute("height");
      canvas.addEventListener("webglcontextlost", function (e) {
        e.preventDefault();
        fail();
      });
      grid.appendChild(canvas);
      glows = imgs.map(function (img) {
        var g = document.createElement("div");
        g.className = "tour-glow";
        g.setAttribute("aria-hidden", "true");
        g.style.backgroundImage = 'url("' + img.getAttribute("src") + '")';
        return grid.insertBefore(g, grid.firstChild);
      });
      tour.style.setProperty("--n", steps.length);
      tour.style.setProperty("--ratio", imgs[0].getAttribute("width") / imgs[0].getAttribute("height"));
      imgs.forEach(function (img) { img.loading = "eager"; });
      mark(0);
      picture(0);
      reveal();
    }
    addEventListener("scroll", onScroll, { passive: true });
    update();
  }

  wide.addEventListener("change", function (e) { live(e.matches); });
  live(wide.matches);
})();
