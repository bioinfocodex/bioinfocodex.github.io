// WebGL hero background for the home page.
(function(){
  const canvas = document.getElementById('shader-canvas');
  if (!canvas) return;
  const gl = canvas.getContext('webgl2');
  if (!gl) return;

  const dpr = Math.max(1, 0.5 * window.devicePixelRatio);
  canvas.width = window.innerWidth * dpr;
  canvas.height = window.innerHeight * dpr;
  gl.viewport(0, 0, canvas.width, canvas.height);

  const vertSrc = `#version 300 es
precision highp float;
in vec4 position;
void main(){gl_Position=position;}`;

  const fragSrc = `#version 300 es
precision highp float;
out vec4 O;
uniform vec2 resolution;
uniform float time;
uniform vec2 mouse;

#define PI 3.14159265
#define T time
#define R resolution

float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float hash1(float p){return fract(sin(p*127.1)*43758.5453);}

float noise(vec2 p){
  vec2 i=floor(p),f=fract(p);
  f=f*f*(3.0-2.0*f);
  return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),
             mix(hash(i+vec2(0,1)),hash(i+1.0),f.x),f.y);
}
float fbm(vec2 p){
  float v=0.0,a=0.5;
  mat2 rot=mat2(cos(0.5),sin(0.5),-sin(0.5),cos(0.5));
  for(int i=0;i<4;i++){v+=a*noise(p);p=rot*p*2.0;a*=0.5;}
  return v;
}

vec3 miniDNA(vec2 uv, vec2 center, float size, float rot, float speed, float seed){
  vec2 d = uv - center;
  float ca=cos(rot), sa=sin(rot);
  d = vec2(d.x*ca - d.y*sa, d.x*sa + d.y*ca);
  d /= size;
  vec3 col = vec3(0.0);
  if(abs(d.x) > 3.0 || abs(d.y) > 2.0) return col;
  float t = T * speed + seed * 10.0;
  float freq = 3.5, amp = 0.6;
  float wave1 = sin(d.x * freq + t) * amp;
  float wave2 = sin(d.x * freq + t + PI) * amp;
  float s1 = smoothstep(0.08, 0.0, abs(d.y - wave1));
  float s2 = smoothstep(0.08, 0.0, abs(d.y - wave2));
  float g1 = 0.01 / (abs(d.y - wave1) + 0.02);
  float g2 = 0.01 / (abs(d.y - wave2) + 0.02);
  float rungX = fract(d.x * freq / (2.0 * PI) + t / (2.0 * PI));
  float rungMask = smoothstep(0.45, 0.5, rungX) * smoothstep(0.55, 0.5, rungX);
  rungMask += smoothstep(0.95, 1.0, rungX) + smoothstep(0.05, 0.0, rungX);
  float minW = min(wave1, wave2), maxW = max(wave1, wave2);
  float inRung = step(minW - 0.03, d.y) * step(d.y, maxW + 0.03) * rungMask;
  float rung = inRung * smoothstep(0.06, 0.0, min(abs(d.y - minW), abs(d.y - maxW)) - abs(maxW-minW)*0.5) * 0.5;
  float edgeFade = smoothstep(2.5, 1.5, abs(d.x));
  vec3 c1 = vec3(0.0, 0.85, 0.6), c2 = vec3(0.35, 0.45, 1.0), cr = vec3(0.1, 0.65, 0.8);
  float hueShift = hash1(seed * 7.7) * 0.5;
  c1 = mix(c1, vec3(0.0, 0.7, 0.9), hueShift);
  c2 = mix(c2, vec3(0.6, 0.3, 0.9), hueShift);
  col += (s1 * 0.8 + g1 * 0.3) * c1 * edgeFade;
  col += (s2 * 0.8 + g2 * 0.3) * c2 * edgeFade;
  col += rung * cr * edgeFade;
  float pPos = fract(t * 0.3 + seed);
  float px2 = mix(-2.0, 2.0, pPos);
  float py = sin(px2 * freq + t) * amp;
  float pDist = length(d - vec2(px2, py));
  col += 0.004 / (pDist + 0.008) * mix(c1, c2, pPos) * edgeFade;
  return col;
}

void main(){
  vec2 uv = (gl_FragCoord.xy - 0.5 * R) / min(R.x, R.y);
  vec2 ms = (mouse - 0.5 * R) / min(R.x, R.y);
  vec3 col = vec3(0.0);
  float bg = fbm(uv * 3.0 + T * 0.03);
  float bg2 = fbm(uv * 4.0 - T * 0.05 + 50.0);
  col += vec3(0.0, bg * 0.025, bg * 0.04);
  col += vec3(bg2 * 0.015, 0.0, bg2 * 0.03);
  for(float i = 0.0; i < 40.0; i++){
    float px = hash1(i * 1.31) * 2.2 - 1.1;
    float py = hash1(i * 2.47 + 5.0) * 1.4 - 0.7;
    px += sin(T * 0.06 + i * 0.7) * 0.08;
    py += cos(T * 0.05 + i * 1.1) * 0.05;
    float sz = 0.02 + hash1(i * 3.89) * 0.04;
    float rot = hash1(i * 5.13) * PI + T * (0.05 + hash1(i*0.77) * 0.1);
    float spd = 0.5 + hash1(i * 4.51) * 1.0;
    float brightness = 0.3 + sz * 8.0;
    col += miniDNA(uv, vec2(px, py), sz, rot, spd, i) * brightness;
  }
  for(float i = 0.0; i < 50.0; i++){
    vec2 pos = vec2(hash1(i*1.71)*2.4-1.2, hash1(i*2.93+10.0)*1.6-0.8);
    pos += vec2(sin(T*0.04+i*0.5), cos(T*0.03+i*0.8)) * 0.02;
    float d = length(uv - pos);
    float twinkle = sin(T*(1.0+hash1(i*3.3)*2.0)+i*5.0)*0.5+0.5;
    float bri = 0.0003 * twinkle / (d + 0.003);
    vec3 ntCol;
    float idx = mod(i, 4.0);
    if(idx < 1.0) ntCol = vec3(0.0, 0.9, 0.5);
    else if(idx < 2.0) ntCol = vec3(0.85, 0.2, 0.3);
    else if(idx < 3.0) ntCol = vec3(0.2, 0.5, 1.0);
    else ntCol = vec3(0.9, 0.8, 0.15);
    col += bri * ntCol;
  }
  float mDist = length(uv - ms);
  col += vec3(0.0, 0.12, 0.08) * 0.04 / (mDist + 0.25);
  float vig = 1.0 - length(uv) * 0.6;
  col *= max(vig, 0.0);
  col = col / (1.0 + col);
  O = vec4(col, 1.0);
}`;

  function compile(sh, src){ gl.shaderSource(sh, src); gl.compileShader(sh);
    if(!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) console.error(gl.getShaderInfoLog(sh));
  }

  const vs = gl.createShader(gl.VERTEX_SHADER);
  const fs = gl.createShader(gl.FRAGMENT_SHADER);
  compile(vs, vertSrc);
  compile(fs, fragSrc);

  const prog = gl.createProgram();
  gl.attachShader(prog, vs);
  gl.attachShader(prog, fs);
  gl.linkProgram(prog);

  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,1,-1,-1,1,1,1,-1]), gl.STATIC_DRAW);
  const pos = gl.getAttribLocation(prog, 'position');
  gl.enableVertexAttribArray(pos);
  gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0);

  const uRes   = gl.getUniformLocation(prog, 'resolution');
  const uTime  = gl.getUniformLocation(prog, 'time');
  const uMouse = gl.getUniformLocation(prog, 'mouse');

  let mouseX = canvas.width/2, mouseY = canvas.height/2;
  window.addEventListener('mousemove', function(e){
    mouseX = e.clientX * dpr;
    mouseY = (window.innerHeight - e.clientY) * dpr;
  });

  function resize(){
    const d = Math.max(1, 0.5 * window.devicePixelRatio);
    canvas.width  = window.innerWidth * d;
    canvas.height = window.innerHeight * d;
    gl.viewport(0, 0, canvas.width, canvas.height);
  }
  window.addEventListener('resize', resize);

  let shaderAnimId = null;
  function loop(now){
    gl.clearColor(0,0,0,1);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(prog);
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.uniform2f(uRes, canvas.width, canvas.height);
    gl.uniform1f(uTime, now * 1e-3);
    gl.uniform2f(uMouse, mouseX, mouseY);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    shaderAnimId = requestAnimationFrame(loop);
  }

  // Each page is its own document now, so there is no page switch to watch:
  // run while the tab is visible, stop when it is not.
  function startShader(){ if(!shaderAnimId){ resize(); shaderAnimId = requestAnimationFrame(loop); } }
  function stopShader(){ if(shaderAnimId){ cancelAnimationFrame(shaderAnimId); shaderAnimId = null; } }
  document.addEventListener('visibilitychange', function(){
    if(document.hidden) stopShader(); else startShader();
  });
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) startShader();
  else { resize(); loop(0); stopShader(); }
})();
