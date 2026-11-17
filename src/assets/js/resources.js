// Network background for the resources hero.
(function(){
  var canvas=document.getElementById('res-net-canvas');
  if(!canvas)return;var ctx=canvas.getContext('2d');if(!ctx)return;
  var dpr=window.devicePixelRatio||1,W=0,H=0;
  var cols=['#00c896','#58a6ff','#7c3aed'],nodes=[];
  function seed(){
    nodes=[];var n=Math.max(28,Math.min(54,Math.round((W*H)/15000)));
    for(var i=0;i<n;i++)nodes.push({x:Math.random(),y:Math.random(),vx:(Math.random()-.5)*.0006,vy:(Math.random()-.5)*.0006,r:2+Math.random()*4.5,c:cols[i%3],ph:Math.random()*6});
  }
  function fit(){
    var host=canvas.parentElement;if(!host)return false;
    var w=host.offsetWidth,h=host.offsetHeight;
    if(w===0||h===0)return false;
    if(w!==W||h!==H){W=w;H=h;canvas.width=w*dpr;canvas.height=h*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);if(!nodes.length)seed();}
    return true;
  }
  var t=0;
  function draw(){
    requestAnimationFrame(draw);
    if(!fit())return;
    ctx.fillStyle='#030510';ctx.fillRect(0,0,W,H);
    for(var i=0;i<nodes.length;i++)for(var j=i+1;j<nodes.length;j++){
      var a=nodes[i],b=nodes[j],dx=(a.x-b.x)*W,dy=(a.y-b.y)*H,d=Math.sqrt(dx*dx+dy*dy);
      if(d<130){ctx.strokeStyle='rgba(88,166,255,'+(0.16*(1-d/130))+')';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(a.x*W,a.y*H);ctx.lineTo(b.x*W,b.y*H);ctx.stroke();}
    }
    for(var k=0;k<nodes.length;k++){var nd=nodes[k];
      nd.x+=nd.vx;nd.y+=nd.vy;if(nd.x<.02||nd.x>.98)nd.vx*=-1;if(nd.y<.04||nd.y>.96)nd.vy*=-1;
      var pulse=0.55+0.45*Math.sin(t+nd.ph);
      ctx.globalAlpha=0.13*pulse;ctx.fillStyle=nd.c;ctx.beginPath();ctx.arc(nd.x*W,nd.y*H,nd.r*3.2,0,7);ctx.fill();
      ctx.globalAlpha=pulse;ctx.beginPath();ctx.arc(nd.x*W,nd.y*H,nd.r,0,7);ctx.fill();ctx.globalAlpha=1;
    }
    t+=0.028;
  }
  draw();
})();
