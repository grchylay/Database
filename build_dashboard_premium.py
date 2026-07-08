#!/usr/bin/env python3
"""Build premium NOC Dashboard with glass-morphism, particles, and animations."""
import json, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "dashboard_data.json")
OUT_PATH  = os.path.join(BASE_DIR, "noc_dashboard.html")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    D = json.load(f)

DATA_JSON = json.dumps(D, ensure_ascii=False)

HTML = fr'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SER DATA LAB - NOC</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root{{
  --bg:#060b14;--surface:#0c1222;--surface2:#111827;
  --border:#1b2740;--border-glow:#00d4aa33;
  --cyan:#00e6b8;--blue:#3b9eff;--purple:#a78bfa;
  --amber:#fbbf24;--red:#f87171;--green:#4ade80;
  --pink:#f472b6;--text:#c8d6e5;--dim:#64748b;
  --glow-cyan:0 0 20px #00e6b844;--glow-blue:0 0 20px #3b9eff44;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{
  background:var(--bg);color:var(--text);
  font-family:'Inter','Microsoft YaHei','PingFang SC',sans-serif;
  min-height:100vh;overflow-x:hidden;
}}

/* ── Animated Background ── */
#bg-canvas{{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;opacity:.6;pointer-events:none}}

/* ── Content wrapper ── */
#app{{position:relative;z-index:1}}

/* ── Header ── */
.header{{
  background:linear-gradient(180deg,#0d1525ee,#060b14ee);
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border-bottom:1px solid var(--border);padding:14px 28px;
  display:flex;align-items:center;justify-content:space-between;
  position:sticky;top:0;z-index:100;gap:12px;flex-wrap:wrap;
}}
.header-l{{display:flex;align-items:center;gap:14px}}
.logo{{
  width:44px;height:44px;border-radius:12px;
  background:linear-gradient(135deg,#00e6b8,#3b9eff);
  display:flex;align-items:center;justify-content:center;
  font-size:20px;font-weight:800;color:#060b14;
  box-shadow:var(--glow-cyan);animation:logoPulse 3s ease-in-out infinite;
}}
@keyframes logoPulse{{0%,100%{{box-shadow:0 0 15px #00e6b866}}50%{{box-shadow:0 0 30px #3b9eff88}}}}
.title-group{{display:flex;flex-direction:column}}
.title{{
  font-size:22px;font-weight:800;letter-spacing:3px;
  background:linear-gradient(90deg,#00e6b8,#3b9eff,#a78bfa);-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;background-size:200% auto;
  animation:titleShine 4s linear infinite;
}}
@keyframes titleShine{{to{{background-position:200% center}}}}
.subtitle{{font-size:11px;color:var(--dim);letter-spacing:2px;text-transform:uppercase}}
.header-r{{display:flex;align-items:center;gap:28px;flex-wrap:wrap}}
.hstat{{text-align:center}}
.hstat .v{{font-size:22px;font-weight:700;color:var(--cyan);font-family:'JetBrains Mono','Consolas',monospace}}
.hstat .l{{font-size:10px;color:var(--dim);text-transform:uppercase;letter-spacing:1px}}
.live-badge{{
  display:flex;align-items:center;gap:8px;padding:6px 14px;
  border-radius:20px;background:#00e6b811;border:1px solid #00e6b833;
  font-size:11px;color:var(--cyan);font-weight:600;letter-spacing:1px;
}}
.live-dot{{width:7px;height:7px;background:var(--cyan);border-radius:50%;
  box-shadow:0 0 10px var(--cyan);animation:pulse 1.5s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.3;transform:scale(1.3)}}}}

/* ── Stats Row ── */
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;padding:16px 24px 0}}
.stat-card{{
  background:linear-gradient(135deg,#0f172a,#0c1322);border:1px solid var(--border);
  border-radius:14px;padding:18px 20px;position:relative;overflow:hidden;
  display:flex;justify-content:space-between;align-items:center;
  transition:all .4s;cursor:default;
}}
.stat-card:hover{{border-color:var(--border-glow);transform:translateY(-2px);
  box-shadow:0 8px 32px #00000044,0 0 0 1px var(--border-glow) inset;}}
.stat-card::before{{
  content:'';position:absolute;top:-30px;right:-30px;width:80px;height:80px;
  border-radius:50%;opacity:.06;transition:all .6s;
}}
.stat-card:hover::before{{transform:scale(1.5);opacity:.12}}
.st0::before{{background:var(--cyan)}}
.st1::before{{background:var(--blue)}}
.st2::before{{background:var(--purple)}}
.st3::before{{background:var(--amber)}}
.stat-icon{{font-size:34px;filter:grayscale(.2);transition:filter .3s}}
.stat-card:hover .stat-icon{{filter:grayscale(0)}}
.stat-info{{text-align:right}}
.stat-val{{font-size:32px;font-weight:800;font-family:'JetBrains Mono','Consolas',monospace;
  transition:color .3s}}
.st0 .stat-val{{color:var(--cyan)}}.st1 .stat-val{{color:var(--blue)}}
.st2 .stat-val{{color:var(--purple)}}.st3 .stat-val{{color:var(--amber)}}
.stat-label{{font-size:10px;color:var(--dim);text-transform:uppercase;letter-spacing:1px;margin-top:4px}}

/* ── Main Grid ── */
.main{{padding:14px 24px 18px;display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}
.c2{{grid-column:span 2}}.c4{{grid-column:span 4}}

/* ── Panel ── */
.panel{{
  background:linear-gradient(180deg,#0f172a,#0a101e);border:1px solid var(--border);
  border-radius:14px;padding:14px 16px;position:relative;overflow:hidden;
  transition:all .4s;
}}
.panel:hover{{border-color:#ffffff15;box-shadow:0 4px 24px #00000033}}
/* Corner accent line */
.panel::after{{
  content:'';position:absolute;top:0;right:0;width:40px;height:40px;
  background:linear-gradient(135deg,transparent 50%,#00e6b811 50%,#00e6b811 60%,transparent 60%);
  border-radius:0 14px 0 0;opacity:0;transition:opacity .4s;
}}
.panel:hover::after{{opacity:1}}
.ph{{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}}
.pt{{font-size:12.5px;font-weight:700;color:var(--text);letter-spacing:.5px;
  display:flex;align-items:center;gap:8px}}
.pt-dot{{width:6px;height:6px;border-radius:50%;display:inline-block;flex-shrink:0}}
.pb{{font-size:9px;background:#ffffff08;color:var(--dim);padding:3px 10px;
  border-radius:12px;letter-spacing:.5px;border:1px solid #ffffff08}}
.chart{{width:100%}}
.ch-md{{height:260px}}.ch-lg{{height:290px}}.ch-sm{{height:200px}}

/* ── Gauges ── */
.gauge-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:6px}}
.gi{{text-align:center}}.gl{{font-size:10px;color:var(--dim);margin-top:-6px;letter-spacing:.5px}}

/* ── Footer ── */
.footer{{text-align:center;padding:12px;font-size:10px;color:#1a2a40;
  border-top:1px solid var(--border);letter-spacing:1px}}

/* ── Responsive ── */
@media(max-width:1000px){{
  .stats{{grid-template-columns:repeat(2,1fr);gap:10px;padding:10px 14px 0}}
  .main{{grid-template-columns:repeat(2,1fr);gap:10px;padding:10px 14px 14px}}
  .c2,.c4{{grid-column:span 2}}
  .stat-val{{font-size:24px}}.stat-icon{{font-size:26px}}
  .title{{font-size:17px}}.header{{padding:10px 14px}}
  .ch-md,.ch-lg{{height:220px}}
}}
@media(max-width:550px){{
  .stats,.main{{grid-template-columns:1fr;gap:8px}}
  .c2,.c4{{grid-column:span 1}}
  .ch-md,.ch-lg,.ch-sm{{height:200px}}
  .gauge-grid{{grid-template-columns:repeat(2,1fr)}}
  .header-r{{gap:12px}} .hstat .v{{font-size:16px}}
}}
</style>
</head>
<body>

<!-- Animated particle background -->
<canvas id="bg-canvas"></canvas>

<!-- App content -->
<div id="app">

<!-- HEADER -->
<header class="header">
  <div class="header-l">
    <div class="logo">N<br>O<br>C</div>
    <div class="title-group">
      <div class="title">SER DATA LAB — NOC</div>
      <div class="subtitle">Data Collection &amp; Monitoring System</div>
    </div>
  </div>
  <div class="header-r">
    <div class="hstat"><div class="v" id="htime">--</div><div class="l">Current Time</div></div>
    <div class="hstat"><div class="v" id="hhosts">--</div><div class="l">Online Hosts</div></div>
    <div class="hstat"><div class="v" id="hrecs">--</div><div class="l">Records</div></div>
    <div class="live-badge"><div class="live-dot"></div>SYSTEM LIVE</div>
  </div>
</header>

<!-- STAT CARDS -->
<div class="stats">
  <div class="stat-card st0"><div class="stat-icon">&#x1F5A5;&#xFE0F;</div><div class="stat-info"><div class="stat-val" id="s1">--</div><div class="stat-label">Online Hosts</div></div></div>
  <div class="stat-card st1"><div class="stat-icon">&#x1F4CA;</div><div class="stat-info"><div class="stat-val" id="s2">--</div><div class="stat-label">Active Metrics</div></div></div>
  <div class="stat-card st2"><div class="stat-icon">&#x1F4BE;</div><div class="stat-info"><div class="stat-val" id="s3">--</div><div class="stat-label">Total Records</div></div></div>
  <div class="stat-card st3"><div class="stat-icon">&#x26A1;</div><div class="stat-info"><div class="stat-val" id="s4">--</div><div class="stat-label">Avg CPU Usage</div></div></div>
</div>

<!-- MAIN GRID -->
<div class="main">

  <!-- R1: CPU Trend (c2) + Location Pie + Type Pie -->
  <div class="panel c2"><div class="ph"><span class="pt"><span class="pt-dot" style="background:var(--cyan);box-shadow:0 0 6px var(--cyan)"></span>CPU Usage Trend</span><span class="pb">6 Hosts &middot; 168 Hours</span></div><div class="chart ch-md" id="cpu-trend"></div></div>
  <div class="panel"><div class="ph"><span class="pt"><span class="pt-dot" style="background:var(--blue);box-shadow:0 0 6px var(--blue)"></span>Location Distribution</span><span class="pb">5 Data Centers</span></div><div class="chart ch-md" id="pie-loc"></div></div>
  <div class="panel"><div class="ph"><span class="pt"><span class="pt-dot" style="background:var(--purple);box-shadow:0 0 6px var(--purple)"></span>Data Type Ratio</span><span class="pb">Disk vs Perf</span></div><div class="chart ch-md" id="pie-dist"></div></div>

  <!-- R2: Gauges row -->
  <div class="panel c4"><div class="ph"><span class="pt"><span class="pt-dot" style="background:var(--amber);box-shadow:0 0 6px var(--amber)"></span>Real-Time System Gauges</span><span class="pb">CPU &middot; Memory &middot; Disk &middot; Load</span></div>
  <div class="gauge-grid">
    <div class="gi"><div class="chart ch-sm" id="g-cpu"></div><div class="gl">CPU Utilization</div></div>
    <div class="gi"><div class="chart ch-sm" id="g-mem"></div><div class="gl">Memory Usage</div></div>
    <div class="gi"><div class="chart ch-sm" id="g-disk"></div><div class="gl">Disk I/O</div></div>
    <div class="gi"><div class="chart ch-sm" id="g-load"></div><div class="gl">System Load</div></div>
  </div></div>

  <!-- R3: CPU Bar (c2) + Process + Disk Top -->
  <div class="panel c2"><div class="ph"><span class="pt"><span class="pt-dot" style="background:var(--red);box-shadow:0 0 6px var(--red)"></span>CPU per Host (Avg vs Peak)</span><span class="pb">20 Servers</span></div><div class="chart ch-lg" id="cpu-bar"></div></div>
  <div class="panel"><div class="ph"><span class="pt"><span class="pt-dot" style="background:var(--green);box-shadow:0 0 6px var(--green)"></span>Process Monitor</span><span class="pb">host001</span></div><div class="chart ch-md" id="proc"></div></div>
  <div class="panel"><div class="ph"><span class="pt"><span class="pt-dot" style="background:var(--amber);box-shadow:0 0 6px var(--amber)"></span>Peak Disk Util</span><span class="pb">sda Top 8</span></div><div class="chart ch-md" id="disk-top"></div></div>

  <!-- R4: Memory (c2) + Network (c2) -->
  <div class="panel c2"><div class="ph"><span class="pt"><span class="pt-dot" style="background:var(--cyan);box-shadow:0 0 6px var(--cyan)"></span>Memory Breakdown</span><span class="pb">host001 &middot; MB</span></div><div class="chart ch-md" id="mem"></div></div>
  <div class="panel c2"><div class="ph"><span class="pt"><span class="pt-dot" style="background:var(--pink);box-shadow:0 0 6px var(--pink)"></span>Network Throughput</span><span class="pb">host001 &middot; MB/s</span></div><div class="chart ch-md" id="net"></div></div>

  <!-- R5: Load (c2) + Disk Trend (c2) -->
  <div class="panel c2"><div class="ph"><span class="pt"><span class="pt-dot" style="background:var(--purple);box-shadow:0 0 6px var(--purple)"></span>Load Average</span><span class="pb">host001 &middot; load1/5/15</span></div><div class="chart ch-md" id="load"></div></div>
  <div class="panel c2"><div class="ph"><span class="pt"><span class="pt-dot" style="background:var(--red);box-shadow:0 0 6px var(--red)"></span>Disk Utilization Trend</span><span class="pb">sda_util Top 5 Hosts</span></div><div class="chart ch-md" id="disk"></div></div>

</div>

<footer class="footer">
  SER DATA LAB &mdash; Network Operations Center &mdash; {D.get('time_range','')} &mdash; All Systems Operational
</footer>

</div><!-- /#app -->

<script>
// ═══════════════════════════════════════════
// PARTICLE BACKGROUND
// ═══════════════════════════════════════════
(function(){{
  var c=document.getElementById('bg-canvas'),ctx=c.getContext('2d');
  var w,h,particles=[];
  function resize(){{w=c.width=window.innerWidth;h=c.height=window.innerHeight}}
  resize();window.addEventListener('resize',resize);

  for(var i=0;i<60;i++)particles.push({{
    x:Math.random()*w,y:Math.random()*h,
    vx:(Math.random()-.5)*.3,vy:(Math.random()-.5)*.3,
    r:Math.random()*1.2+.3,alpha:Math.random()*.5+.2
  }});

  function draw(){{
    ctx.clearRect(0,0,w,h);
    // Grid lines
    ctx.strokeStyle='#1a2a4020';ctx.lineWidth=.5;
    var gs=60;
    for(var x=gs;x<w;x+=gs){{ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke()}}
    for(var y=gs;y<h;y+=gs){{ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke()}}

    // Particles
    particles.forEach(function(p){{
      p.x+=p.vx;p.y+=p.vy;
      if(p.x<0)p.x=w;if(p.x>w)p.x=0;
      if(p.y<0)p.y=h;if(p.y>h)p.y=0;
      ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle='rgba(0,212,170,'+p.alpha+')';ctx.fill();
    }});
    // Connections
    particles.forEach(function(a,i){{
      particles.slice(i+1).forEach(function(b){{
        var dx=a.x-b.x,dy=a.y-b.y,dist=Math.sqrt(dx*dx+dy*dy);
        if(dist<120){{
          ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);
          ctx.strokeStyle='rgba(0,180,216,'+(.08*(1-dist/120))+')';
          ctx.lineWidth=.3;ctx.stroke();
        }}
      }});
    }});
    requestAnimationFrame(draw);
  }}
  draw();
}})();

// ═══════════════════════════════════════════
// DATA & ECHARTS
// ═══════════════════════════════════════════
var D={DATA_JSON};
var BG='#0a101e00',BDR='#1b2740',TXT='#b0c4d8',DIM='#506680';
var CY='#00e6b8',BL='#3b9eff',PR='#a78bfa',AM='#fbbf24',RD='#f87171',GN='#4ade80',PK='#f472b6';
var COLS=[CY,BL,PR,AM,RD,'#48dbfb',PK,'#fb923c','#38bdf8',GN];

function dark(opt){{
  return Object.assign({{backgroundColor:'transparent',textStyle:{{color:TXT}},
    legend:{{textStyle:{{color:DIM,fontSize:10}},icon:'roundRect',itemWidth:10,itemHeight:6,top:0}},
    tooltip:{{backgroundColor:'#0f172aee',borderColor:BDR,textStyle:{{color:TXT,fontSize:11}},
      extraCssText:'border-radius:8px;box-shadow:0 8px 32px #00000066'}}
  }},opt);
}}

function ls(obj,name,color,area,width){{
  var d=obj||{{values:[],times:[]}};
  return {{name:name,type:'line',data:d.values||[],smooth:true,symbol:'none',
    lineStyle:{{color:color,width:width||1.5}},
    itemStyle:{{color:color}},
    areaStyle:area?{{color:new echarts.graphic.LinearGradient(0,0,0,1,[
      {{offset:0,color:color+'33'}},{{offset:1,color:color+'00'}}])}}:undefined}};
}}

function ts(arr){{if(!arr||!arr.length)return[];return arr.map(function(t){{return t.length>5?t.substring(5):t}})}}
function ti(arr){{return Math.max(1,Math.floor((arr||[]).length/8))}}

// Smooth gradient for bars
function barGrad(c1,c2){{return new echarts.graphic.LinearGradient(0,0,0,1,[
  {{offset:0,color:c1}},{{offset:1,color:c2+'44'}}])}}

// ── 1. CPU Trend ──
(function(){{
  var hosts=['host001','host002','host003','host004','host005','host006'];
  var series=hosts.map(function(h,i){{return ls(D.cpu_trend[h],h,COLS[i],i===0,1.8);}});
  var t=(D.cpu_trend.host001||{{}}).times||[];
  var opt=dark({{tooltip:{{trigger:'axis'}},legend:{{data:hosts,bottom:0}},
    grid:{{left:42,right:14,top:8,bottom:28}},
    xAxis:{{type:'category',data:ts(t),axisLine:{{lineStyle:{{color:BDR}}}},
      axisLabel:{{color:DIM,fontSize:9,interval:ti(t)}}}},
    yAxis:{{type:'value',name:'%',splitLine:{{lineStyle:{{color:'#ffffff06'}}}}}},
    series:series}});
  echarts.init(document.getElementById('cpu-trend')).setOption(opt);
}})();

// ── 2. Location Pie ──
(function(){{
  var opt=dark({{tooltip:{{trigger:'item',formatter:'{{b}}: {{c}} ({{d}}%)'}},
    series:[{{type:'pie',radius:['48%','78%'],center:['50%','54%'],
      data:D.pie_location,label:{{color:TXT,fontSize:10}},
      emphasis:{{label:{{fontSize:18,fontWeight:'bold'}},scaleSize:8}},
      itemStyle:{{borderColor:BG,borderWidth:4,borderRadius:3}}}}]}});
  echarts.init(document.getElementById('pie-loc')).setOption(opt);
}})();

// ── 3. Type Pie ──
(function(){{
  var opt=dark({{tooltip:{{trigger:'item',formatter:'{{b}}: {{c}} ({{d}}%)'}},
    series:[{{type:'pie',radius:['48%','78%'],center:['50%','54%'],
      data:D.pie_dist,label:{{color:TXT,fontSize:10}},
      emphasis:{{label:{{fontSize:18,fontWeight:'bold'}},scaleSize:8}},
      itemStyle:{{borderColor:BG,borderWidth:4,borderRadius:3}}}}]}});
  echarts.init(document.getElementById('pie-dist')).setOption(opt);
}})();

// ── 4. Gauges ──
function gauge(id,val,color,unit,ticks){{
  var m=ticks||100;
  var opt={{series:[{{type:'gauge',radius:'85%',center:['50%','54%'],
    startAngle:210,endAngle:-30,min:0,max:m,splitNumber:10,
    progress:{{show:true,width:8,roundCap:true,itemStyle:{{color:color}}}},
    axisLine:{{show:true,lineStyle:{{width:8,color:[[val/m,color],[1,'#ffffff08']]}}}},
    axisTick:{{show:false}},splitLine:{{show:false}},axisLabel:{{show:false}},
    pointer:{{show:false}},
    detail:{{valueAnimation:true,formatter:'{{value}}'+unit,fontSize:18,
      color:TXT,offsetCenter:[0,'62%'],fontWeight:700,fontFamily:"'JetBrains Mono',monospace"}},
    data:[{{value:val}}],title:{{show:false}}}}]}};
  echarts.init(document.getElementById(id)).setOption(opt);
}}
setTimeout(function(){{
  gauge('g-cpu',D.gauge_cpu,'#00e6b8','%',100);
  gauge('g-mem',D.gauge_mem,'#3b9eff','%',100);
  gauge('g-disk',D.gauge_disk,'#fbbf24','%',100);
  gauge('g-load',Math.min(D.gauge_load*10,100),'#a78bfa','',100);
}},200);

// ── 5. CPU Bar ──
(function(){{
  var opt=dark({{tooltip:{{trigger:'axis'}},legend:{{data:['Average','Peak'],bottom:0}},
    grid:{{left:42,right:14,top:8,bottom:28}},
    xAxis:{{type:'category',data:D.cpu_bar.hosts,axisLabel:{{color:DIM,fontSize:9,rotate:30}}}},
    yAxis:{{type:'value',name:'%',splitLine:{{lineStyle:{{color:'#ffffff06'}}}}}},
    series:[
      {{name:'Average',type:'bar',data:D.cpu_bar.avg,barWidth:'50%',barGap:'20%',
        itemStyle:{{color:barGrad('#00e6b8','#00e6b8'),borderRadius:[4,4,0,0]}}}},
      {{name:'Peak',type:'bar',data:D.cpu_bar.peak,barWidth:'50%',
        itemStyle:{{color:barGrad('#f87171','#f87171'),borderRadius:[4,4,0,0]}}}}
    ]}});
  echarts.init(document.getElementById('cpu-bar')).setOption(opt);
}})();

// ── 6. Process ──
(function(){{
  var mods=[{{k:'proc_total',l:'Total',c:CY}},{{k:'proc_run',l:'Running',c:GN}},{{k:'proc_block',l:'Blocked',c:RD}}];
  var series=mods.map(function(m){{return ls(D['proc_'+m.k],m.l,m.c,m.k==='proc_total',1.5);}});
  var times=(D.proc_proc_total||{{}}).times||[];
  var opt=dark({{tooltip:{{trigger:'axis'}},legend:{{data:mods.map(function(m){{return m.l}}),bottom:0}},
    grid:{{left:42,right:8,top:8,bottom:28}},
    xAxis:{{type:'category',data:ts(times),axisLabel:{{color:DIM,fontSize:9,interval:ti(times)}}}},
    yAxis:{{type:'value',splitLine:{{lineStyle:{{color:'#ffffff06'}}}}}},series:series}});
  echarts.init(document.getElementById('proc')).setOption(opt);
}})();

// ── 7. Disk Top Peaks ──
(function(){{
  var hosts=(D.disk_top_hosts||[]).slice(0,8);
  var vals=hosts.map(function(h){{var d=D['disk_'+h]||{{values:[]}};
    return d.values?Math.round(Math.max.apply(null,d.values)*10)/10:0;}});
  var maxV=Math.max.apply(null,vals);
  var colors=vals.map(function(v){{return v>95?RD:v>85?AM:BL;}});
  var opt=dark({{
    grid:{{left:65,right:16,top:5,bottom:8}},
    xAxis:{{type:'value',name:'%',max:100,splitLine:{{lineStyle:{{color:'#ffffff06'}}}}}},
    yAxis:{{type:'category',data:hosts,inverse:true,axisLabel:{{color:TXT,fontSize:9,fontWeight:600}}}},
    series:[{{type:'bar',data:vals.map(function(v,i){{return{{
      value:v,itemStyle:{{
        color:new echarts.graphic.LinearGradient(0,0,1,0,[
          {{offset:0,color:colors[i]+'88'}},{{offset:1,color:colors[i]}}]),
        borderRadius:[0,6,6,0]}}}};
    }}),
      label:{{show:true,position:'right',color:TXT,fontSize:9,fontWeight:600,formatter:'{{c}}%'}}}}]
  }});
  echarts.init(document.getElementById('disk-top')).setOption(opt);
}})();

// ── 8. Memory ──
(function(){{
  var mods=[{{k:'mem_used',l:'Used',c:CY}},{{k:'mem_free',l:'Free',c:GN}},
            {{k:'mem_buff',l:'Buffer',c:PR}},{{k:'mem_cache',l:'Cache',c:AM}}];
  var series=mods.map(function(m){{return ls(D['mem_'+m.k],m.l,m.c,m.k==='mem_used',1.5);}});
  var times=(D.mem_mem_used||{{}}).times||[];
  var opt=dark({{tooltip:{{trigger:'axis'}},legend:{{data:mods.map(function(m){{return m.l}}),bottom:0}},
    grid:{{left:52,right:10,top:8,bottom:28}},
    xAxis:{{type:'category',data:ts(times),axisLabel:{{color:DIM,fontSize:9,interval:ti(times)}}}},
    yAxis:{{type:'value',name:'MB',splitLine:{{lineStyle:{{color:'#ffffff06'}}}}}},series:series}});
  echarts.init(document.getElementById('mem')).setOption(opt);
}})();

// ── 9. Network ──
(function(){{
  var mods=[{{k:'net_in',l:'Inbound',c:CY}},{{k:'net_out',l:'Outbound',c:PK}}];
  var series=mods.map(function(m){{return ls(D['net_'+m.k],m.l,m.c,true,1.8);}});
  var times=(D.net_net_in||{{}}).times||[];
  var opt=dark({{tooltip:{{trigger:'axis'}},legend:{{data:mods.map(function(m){{return m.l}}),bottom:0}},
    grid:{{left:52,right:10,top:8,bottom:28}},
    xAxis:{{type:'category',data:ts(times),axisLabel:{{color:DIM,fontSize:9,interval:ti(times)}}}},
    yAxis:{{type:'value',name:'MB/s',splitLine:{{lineStyle:{{color:'#ffffff06'}}}}}},series:series}});
  echarts.init(document.getElementById('net')).setOption(opt);
}})();

// ── 10. Load ──
(function(){{
  var mods=[{{k:'load1',l:'load1',c:CY}},{{k:'load5',l:'load5',c:AM}},{{k:'load15',l:'load15',c:RD}}];
  var series=mods.map(function(m){{return ls(D['load_'+m.k],m.l,m.c,false,1.5);}});
  var times=(D.load_load1||{{}}).times||[];
  var opt=dark({{tooltip:{{trigger:'axis'}},legend:{{data:mods.map(function(m){{return m.l}}),bottom:0}},
    grid:{{left:42,right:10,top:8,bottom:28}},
    xAxis:{{type:'category',data:ts(times),axisLabel:{{color:DIM,fontSize:9,interval:ti(times)}}}},
    yAxis:{{type:'value',splitLine:{{lineStyle:{{color:'#ffffff06'}}}}}},series:series}});
  echarts.init(document.getElementById('load')).setOption(opt);
}})();

// ── 11. Disk Trend ──
(function(){{
  var hosts=D.disk_top_hosts||[];
  var series=hosts.map(function(h,i){{return ls(D['disk_'+h],h,COLS[i],false,1.2);}});
  var times=((D['disk_'+(hosts[0]||'')]||{{}}).times||[]);
  var opt=dark({{tooltip:{{trigger:'axis'}},legend:{{data:hosts,bottom:0}},
    grid:{{left:42,right:10,top:8,bottom:28}},
    xAxis:{{type:'category',data:ts(times),axisLabel:{{color:DIM,fontSize:9,interval:ti(times),rotate:20}}}},
    yAxis:{{type:'value',name:'%',max:100,splitLine:{{lineStyle:{{color:'#ffffff06'}}}}}},series:series}});
  echarts.init(document.getElementById('disk')).setOption(opt);
}})();

// ── HEADER STATS ──
(function tick(){{
  var n=new Date();
  document.getElementById('htime').textContent=
    n.getFullYear()+'-'+String(n.getMonth()+1).padStart(2,'0')+'-'+
    String(n.getDate()).padStart(2,'0')+' '+
    String(n.getHours()).padStart(2,'0')+':'+
    String(n.getMinutes()).padStart(2,'0')+':'+
    String(n.getSeconds()).padStart(2,'0');
  setTimeout(tick,1000);
}})();
document.getElementById('hhosts').textContent=D.total_hosts;
document.getElementById('hrecs').textContent=(D.total_records/10000).toFixed(1)+'w';
document.getElementById('s1').textContent=D.total_hosts;
document.getElementById('s2').textContent=D.total_metrics;
document.getElementById('s3').textContent=(D.total_records/1000).toFixed(0)+'k';
document.getElementById('s4').textContent=D.avg_cpu+'%';

// ── RESIZE ──
window.addEventListener('resize',function(){{
  document.querySelectorAll('.chart').forEach(function(el){{
    var i=echarts.getInstanceByDom(el);if(i)i.resize();
  }});
}});
</script>
</body>
</html>'''

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"[OK] Premium dashboard -> {OUT_PATH}")
print(f"     Size: {os.path.getsize(OUT_PATH)/1024:.0f} KB")
