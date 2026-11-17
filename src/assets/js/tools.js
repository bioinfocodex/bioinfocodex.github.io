// Dotted wave background for the tools hero.
(function(){
  const canvas = document.getElementById('tools-dots-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const AMOUNTX = 50, AMOUNTY = 50, SEPARATION = 28;
  let count = 0, mouseX = 0, mouseY = 0, animId = null;

  function resize(){
    const hero = canvas.parentElement;
    if (!hero) return;
    canvas.width = hero.offsetWidth;
    canvas.height = hero.offsetHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  canvas.parentElement.addEventListener('mousemove', function(e){
    const rect = canvas.getBoundingClientRect();
    mouseX = (e.clientX - rect.left - rect.width/2) * 0.5;
    mouseY = (e.clientY - rect.top - rect.height/2) * 0.3;
  });

  function draw(){
    animId = requestAnimationFrame(draw);
    const w = canvas.width, h = canvas.height;
    const halfW = w / 2, halfH = h / 2;

    ctx.fillStyle = 'rgba(3,5,16,1)';
    ctx.fillRect(0, 0, w, h);

    const camY = 350 + mouseY;
    const fov = 600;

    for(let ix = 0; ix < AMOUNTX; ix++){
      for(let iy = 0; iy < AMOUNTY; iy++){
        const wx = ix * SEPARATION - ((AMOUNTX * SEPARATION) / 2);
        const wz = iy * SEPARATION - ((AMOUNTY * SEPARATION) / 2);
        const wy = (Math.sin((ix + count) * 0.3) * 50) +
                   (Math.sin((iy + count) * 0.5) * 50);

        const dx = wx + mouseX * 0.3;
        const dy = wy - camY;
        const dz = wz + 1200;
        if(dz <= 0) continue;

        const scale = fov / dz;
        const sx = dx * scale + halfW;
        const sy = dy * scale + halfH;

        if(sx < -20 || sx > w+20 || sy < -20 || sy > h+20) continue;

        const depthN = Math.max(0, Math.min(1, 1 - dz / 3000));
        const dotSz = Math.max(0.5, 3 * scale);
        const alpha = depthN * 0.9 + 0.1;

        const hue = (wy + 50) / 100;
        let r, g, b;
        if(hue > 0.5){
          const t = (hue - 0.5) * 2;
          r = 0*(1-t)+30*t|0; g = 200*(1-t)+160*t|0; b = 150*(1-t)+255*t|0;
        } else {
          const t = hue * 2;
          r = 100*(1-t)|0; g = 60*(1-t)+200*t|0; b = 200*(1-t)+150*t|0;
        }

        ctx.beginPath();
        ctx.arc(sx, sy, dotSz, 0, 6.283);
        ctx.fillStyle = `rgba(${r},${g},${b},${(alpha*0.9).toFixed(2)})`;
        ctx.fill();

        if(dotSz > 1){
          ctx.beginPath();
          ctx.arc(sx, sy, dotSz * 2.5, 0, 6.283);
          ctx.fillStyle = `rgba(${r},${g},${b},${(alpha*0.08).toFixed(3)})`;
          ctx.fill();
        }
      }
    }
    count += 0.07;
  }

  function startDots(){ resize(); if(!animId) draw(); }
  function stopDots(){ if(animId){ cancelAnimationFrame(animId); animId = null; } }
  document.addEventListener('visibilitychange', function(){
    if(document.hidden) stopDots(); else startDots();
  });
  startDots();
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) stopDots();
})();
