"""
Replaces the entire heatmap section in app.py with a clean, responsive version.
Run from C:\\Users\\WAFI\\irish-property-insights:
    python fix_heatmap_final.py
"""

import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

OLD_START = "<!-- ── HEATMAP SECTION ── -->"
OLD_END   = "<!-- ── END HEATMAP SECTION ── -->"

start_idx = content.find(OLD_START)
end_idx   = content.find(OLD_END)

if start_idx == -1 or end_idx == -1:
    print("ERROR: Could not find heatmap section markers in app.py")
    print(f"  START found: {start_idx != -1}")
    print(f"  END found:   {end_idx != -1}")
    exit(1)

end_idx += len(OLD_END)

NEW_HEATMAP = '''<!-- ── HEATMAP SECTION ── -->
<section style="background:#0a0c0f;padding:4rem 2rem;border-top:1px solid #1a1c20;">
  <div style="max-width:1100px;margin:0 auto;">

    <!-- Header -->
    <div style="text-align:center;margin-bottom:2rem;">
      <div style="display:inline-block;font-size:0.7rem;font-weight:500;letter-spacing:0.18em;text-transform:uppercase;color:#c9a84c;border:1px solid #c9a84c;padding:0.3rem 0.8rem;border-radius:2px;margin-bottom:1rem;">Interactive Map</div>
      <h2 style="font-family:'Playfair Display',serif;font-size:clamp(1.5rem,3vw,2.2rem);font-weight:900;color:white;line-height:1.1;margin-bottom:0.6rem;">Irish Property Investment Heatmap</h2>
      <p style="color:#9a9690;font-size:0.9rem;font-weight:300;max-width:480px;margin:0 auto;">Click any county to see yield, growth and risk. Full micro-area rankings in the report.</p>
    </div>

    <!-- Metric toggle -->
    <div style="display:flex;justify-content:center;margin-bottom:2rem;">
      <div style="display:flex;background:#1a1c20;border:1px solid #2a2c30;border-radius:3px;padding:0.25rem;">
        <button onclick="setMetric(\'yield\',this)" class="hm-btn active-btn" style="padding:0.45rem 1.2rem;border:none;border-radius:2px;font-family:inherit;font-size:0.75rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;background:#c9a84c;color:#0f1014;transition:all 0.2s;">Rental Yield</button>
        <button onclick="setMetric(\'growth\',this)" class="hm-btn" style="padding:0.45rem 1.2rem;border:none;border-radius:2px;font-family:inherit;font-size:0.75rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;background:transparent;color:#6b6860;transition:all 0.2s;">5yr Growth</button>
        <button onclick="setMetric(\'risk\',this)" class="hm-btn" style="padding:0.45rem 1.2rem;border:none;border-radius:2px;font-family:inherit;font-size:0.75rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;background:transparent;color:#6b6860;transition:all 0.2s;">Risk Score</button>
      </div>
    </div>

    <!-- Map + Sidebar grid -->
    <div id="hm-layout" style="display:grid;grid-template-columns:1fr 280px;gap:2rem;align-items:start;">

      <!-- MAP PANEL -->
      <div style="background:#111316;border:1px solid #1a1c20;border-radius:4px;padding:1.5rem;display:flex;align-items:center;justify-content:center;">
        <svg id="hm-svg" viewBox="0 0 320 340" xmlns="http://www.w3.org/2000/svg"
             style="width:100%;height:auto;display:block;max-height:600px;">

          <!-- DONEGAL -->
          <path id="hm-Donegal"   onclick="hmSel(\'Donegal\')"   class="hmc" d="M55,15 L130,8 L165,22 L172,48 L152,68 L128,82 L98,74 L68,54 L50,36 Z"/>
          <!-- MAYO -->
          <path id="hm-Mayo"      onclick="hmSel(\'Mayo\')"      class="hmc" d="M15,88 L60,75 L88,70 L98,93 L82,113 L65,108 L50,128 L24,136 L10,118 Z"/>
          <!-- SLIGO -->
          <path id="hm-Sligo"     onclick="hmSel(\'Sligo\')"     class="hmc" d="M78,75 L108,68 L122,80 L124,96 L106,106 L84,104 L70,92 Z"/>
          <!-- LEITRIM -->
          <path id="hm-Leitrim"   onclick="hmSel(\'Leitrim\')"   class="hmc" d="M122,68 L148,62 L162,76 L158,98 L140,108 L124,106 L122,92 Z"/>
          <!-- CAVAN -->
          <path id="hm-Cavan"     onclick="hmSel(\'Cavan\')"     class="hmc" d="M158,65 L192,58 L208,72 L206,94 L186,102 L164,98 L158,82 Z"/>
          <!-- MONAGHAN -->
          <path id="hm-Monaghan"  onclick="hmSel(\'Monaghan\')"  class="hmc" d="M208,62 L238,56 L252,72 L246,90 L222,94 L206,86 Z"/>
          <!-- LOUTH -->
          <path id="hm-Louth"     onclick="hmSel(\'Louth\')"     class="hmc" d="M246,66 L272,62 L284,82 L272,102 L248,102 L236,88 Z"/>
          <!-- ROSCOMMON -->
          <path id="hm-Roscommon" onclick="hmSel(\'Roscommon\')" class="hmc" d="M96,113 L126,106 L144,116 L140,140 L122,150 L100,148 L88,134 Z"/>
          <!-- LONGFORD -->
          <path id="hm-Longford"  onclick="hmSel(\'Longford\')"  class="hmc" d="M148,98 L174,94 L184,108 L180,126 L160,132 L144,122 Z"/>
          <!-- WESTMEATH -->
          <path id="hm-Westmeath" onclick="hmSel(\'Westmeath\')" class="hmc" d="M174,94 L204,90 L218,104 L214,122 L194,130 L176,124 L180,108 Z"/>
          <!-- MEATH -->
          <path id="hm-Meath"     onclick="hmSel(\'Meath\')"     class="hmc" d="M206,92 L238,88 L256,104 L250,130 L226,136 L206,128 L206,108 Z"/>
          <!-- DUBLIN -->
          <path id="hm-Dublin"    onclick="hmSel(\'Dublin\')"    class="hmc" d="M256,100 L286,94 L300,116 L292,142 L266,148 L250,134 Z"/>
          <!-- GALWAY -->
          <path id="hm-Galway"    onclick="hmSel(\'Galway\')"    class="hmc" d="M14,146 L52,136 L80,126 L94,138 L90,162 L72,178 L46,180 L18,166 Z"/>
          <!-- OFFALY -->
          <path id="hm-Offaly"    onclick="hmSel(\'Offaly\')"    class="hmc" d="M148,132 L180,126 L194,140 L190,156 L166,162 L148,154 Z"/>
          <!-- KILDARE -->
          <path id="hm-Kildare"   onclick="hmSel(\'Kildare\')"   class="hmc" d="M214,128 L246,124 L260,142 L252,164 L228,168 L212,154 Z"/>
          <!-- WICKLOW -->
          <path id="hm-Wicklow"   onclick="hmSel(\'Wicklow\')"   class="hmc" d="M266,144 L296,138 L308,158 L300,182 L276,190 L258,176 Z"/>
          <!-- LAOIS -->
          <path id="hm-Laois"     onclick="hmSel(\'Laois\')"     class="hmc" d="M176,158 L208,152 L220,166 L214,184 L192,190 L174,182 Z"/>
          <!-- CLARE -->
          <path id="hm-Clare"     onclick="hmSel(\'Clare\')"     class="hmc" d="M46,184 L76,176 L94,164 L108,174 L112,192 L100,210 L76,216 L50,206 Z"/>
          <!-- TIPPERARY -->
          <path id="hm-Tipperary" onclick="hmSel(\'Tipperary\')" class="hmc" d="M108,174 L140,168 L164,172 L178,190 L170,212 L150,220 L124,216 L108,202 Z"/>
          <!-- CARLOW -->
          <path id="hm-Carlow"    onclick="hmSel(\'Carlow\')"    class="hmc" d="M214,182 L238,178 L248,194 L240,210 L220,212 L210,198 Z"/>
          <!-- KILKENNY -->
          <path id="hm-Kilkenny"  onclick="hmSel(\'Kilkenny\')"  class="hmc" d="M176,206 L208,200 L224,212 L220,232 L200,240 L176,232 Z"/>
          <!-- LIMERICK -->
          <path id="hm-Limerick"  onclick="hmSel(\'Limerick\')"  class="hmc" d="M74,224 L108,216 L130,220 L140,238 L128,254 L104,260 L78,250 L68,238 Z"/>
          <!-- WATERFORD -->
          <path id="hm-Waterford" onclick="hmSel(\'Waterford\')" class="hmc" d="M150,224 L180,216 L202,222 L206,240 L188,254 L162,258 L146,244 Z"/>
          <!-- WEXFORD -->
          <path id="hm-Wexford"   onclick="hmSel(\'Wexford\')"   class="hmc" d="M206,236 L234,228 L250,244 L246,268 L222,274 L200,262 L200,244 Z"/>
          <!-- KERRY -->
          <path id="hm-Kerry"     onclick="hmSel(\'Kerry\')"     class="hmc" d="M34,258 L68,250 L80,268 L74,294 L52,308 L28,304 L16,282 L22,264 Z"/>
          <!-- CORK -->
          <path id="hm-Cork"      onclick="hmSel(\'Cork\')"      class="hmc" d="M80,264 L118,256 L150,260 L168,270 L170,292 L156,308 L124,318 L92,314 L68,300 L66,278 Z"/>

          <!-- LABELS -->
          <text x="108" y="46"  font-size="9"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none" font-weight="600">Donegal</text>
          <text x="50"  y="108" font-size="8"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none" font-weight="600">Mayo</text>
          <text x="98"  y="90"  font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Sligo</text>
          <text x="140" y="88"  font-size="6.5" fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Leitrim</text>
          <text x="182" y="84"  font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Cavan</text>
          <text x="226" y="78"  font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Monaghan</text>
          <text x="260" y="86"  font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Louth</text>
          <text x="116" y="132" font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Roscommon</text>
          <text x="162" y="116" font-size="6.5" fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Longford</text>
          <text x="196" y="112" font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Westmeath</text>
          <text x="230" y="114" font-size="7.5" fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Meath</text>
          <text x="274" y="122" font-size="8"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Dublin</text>
          <text x="52"  y="156" font-size="8"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Galway</text>
          <text x="168" y="146" font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Offaly</text>
          <text x="234" y="148" font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Kildare</text>
          <text x="282" y="164" font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Wicklow</text>
          <text x="196" y="172" font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Laois</text>
          <text x="80"  y="196" font-size="7.5" fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Clare</text>
          <text x="140" y="196" font-size="8"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Tipperary</text>
          <text x="228" y="198" font-size="6.5" fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Carlow</text>
          <text x="198" y="220" font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Kilkenny</text>
          <text x="104" y="238" font-size="7.5" fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Limerick</text>
          <text x="176" y="238" font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Waterford</text>
          <text x="222" y="252" font-size="7"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Wexford</text>
          <text x="46"  y="280" font-size="8"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Kerry</text>
          <text x="118" y="286" font-size="9"   fill="rgba(255,255,255,0.75)" text-anchor="middle" pointer-events="none">Cork</text>
        </svg>
      </div>

      <!-- SIDEBAR -->
      <div style="display:flex;flex-direction:column;gap:1rem;">
        <!-- Info card -->
        <div id="hm-info" style="background:#1a1c20;border:1px solid #2a2c30;border-radius:4px;padding:2rem;text-align:center;color:#4a4845;font-size:0.85rem;line-height:1.7;">
          <div style="font-size:2rem;margin-bottom:0.5rem;">🗺️</div>
          Click any county on the map to see its investment data
        </div>
        <!-- Legend -->
        <div style="background:#1a1c20;border:1px solid #2a2c30;border-radius:4px;padding:1rem;">
          <div style="font-size:0.65rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.5rem;" id="hm-leg-title">Rental Yield</div>
          <div style="height:6px;border-radius:2px;background:linear-gradient(to right,#0d3d22,#1a6b3c,#c9a84c,#d4821a,#c0392b);margin-bottom:0.4rem;"></div>
          <div style="display:flex;justify-content:space-between;font-size:0.65rem;color:#4a4845;">
            <span id="hm-leg-lo">Low (3%)</span><span id="hm-leg-hi">High (8%+)</span>
          </div>
        </div>
        <!-- Rankings -->
        <div style="background:#1a1c20;border:1px solid #2a2c30;border-radius:4px;overflow:hidden;">
          <div style="padding:0.6rem 1rem;font-size:0.65rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;border-bottom:1px solid #2a2c30;" id="hm-rank-title">Top Counties by Yield</div>
          <div id="hm-rank-list"></div>
        </div>
      </div>
    </div><!-- end grid -->
  </div>
</section>

<style>
.hmc{stroke:#111316;stroke-width:1;cursor:pointer;transition:filter 0.12s,stroke 0.12s,stroke-width 0.12s;}
.hmc:hover{filter:brightness(1.35);stroke:white;stroke-width:2;}
.hmc.hm-sel{stroke:white;stroke-width:2.5;filter:brightness(1.4);}
.hm-btn{transition:background 0.2s,color 0.2s;}
@media(max-width:720px){
  #hm-layout{grid-template-columns:1fr !important;}
}
</style>

<script>
const hmD={
  Dublin:{yield:5.5,growth:5.3,risk:\'Medium\',signal:\'STRONG BUY\',price:484581},
  Cork:{yield:5.1,growth:6.2,risk:\'Low\',signal:\'STRONG BUY\',price:320000},
  Galway:{yield:4.8,growth:5.8,risk:\'Low\',signal:\'STRONG BUY\',price:285000},
  Kildare:{yield:4.2,growth:6.8,risk:\'Low\',signal:\'STRONG BUY\',price:355000},
  Meath:{yield:4.5,growth:7.1,risk:\'Low\',signal:\'STRONG BUY\',price:320000},
  Wicklow:{yield:3.9,growth:5.5,risk:\'Low\',signal:\'MODERATE\',price:380000},
  Limerick:{yield:5.4,growth:6.9,risk:\'Low\',signal:\'STRONG BUY\',price:245000},
  Waterford:{yield:5.2,growth:5.1,risk:\'Medium\',signal:\'STRONG BUY\',price:220000},
  Louth:{yield:5.0,growth:7.1,risk:\'Low\',signal:\'STRONG BUY\',price:235000},
  Wexford:{yield:4.6,growth:6.3,risk:\'Low\',signal:\'STRONG BUY\',price:210000},
  Kilkenny:{yield:4.4,growth:5.8,risk:\'Low\',signal:\'MODERATE\',price:230000},
  Tipperary:{yield:5.8,growth:4.2,risk:\'Medium\',signal:\'MODERATE\',price:175000},
  Clare:{yield:5.3,growth:5.6,risk:\'Low\',signal:\'STRONG BUY\',price:195000},
  Kerry:{yield:4.9,growth:6.1,risk:\'Medium\',signal:\'STRONG BUY\',price:215000},
  Mayo:{yield:6.2,growth:3.8,risk:\'Medium\',signal:\'MODERATE\',price:145000},
  Sligo:{yield:5.9,growth:4.1,risk:\'Medium\',signal:\'MODERATE\',price:155000},
  Donegal:{yield:6.5,growth:3.5,risk:\'High\',signal:\'MODERATE\',price:125000},
  Roscommon:{yield:6.8,growth:3.2,risk:\'High\',signal:\'AVOID\',price:115000},
  Laois:{yield:5.1,growth:5.9,risk:\'Low\',signal:\'STRONG BUY\',price:185000},
  Offaly:{yield:5.3,growth:5.2,risk:\'Medium\',signal:\'MODERATE\',price:165000},
  Westmeath:{yield:5.0,growth:5.4,risk:\'Low\',signal:\'STRONG BUY\',price:175000},
  Longford:{yield:7.1,growth:2.8,risk:\'High\',signal:\'AVOID\',price:95000},
  Cavan:{yield:6.1,growth:3.6,risk:\'High\',signal:\'AVOID\',price:130000},
  Monaghan:{yield:5.7,growth:4.0,risk:\'Medium\',signal:\'MODERATE\',price:140000},
  Carlow:{yield:5.2,growth:6.1,risk:\'Low\',signal:\'STRONG BUY\',price:190000},
  Leitrim:{yield:7.8,growth:2.5,risk:\'High\',signal:\'AVOID\',price:85000}
};

let hmM=\'yield\', hmS=null;

function hmClr(n,m){
  const d=hmD[n]; if(!d) return\'#1a1c20\';
  if(m===\'yield\'){const v=d.yield;if(v>=7)return\'#c0392b\';if(v>=6)return\'#d4821a\';if(v>=5.5)return\'#b8962e\';if(v>=5)return\'#2d8a5e\';if(v>=4)return\'#1a6b3c\';return\'#0d3d22\';}
  if(m===\'growth\'){const v=d.growth;if(v>=7)return\'#1a6b3c\';if(v>=6)return\'#2d8a5e\';if(v>=5)return\'#b8962e\';if(v>=4)return\'#d4821a\';return\'#c0392b\';}
  if(d.risk===\'Low\')return\'#1a6b3c\';if(d.risk===\'Medium\')return\'#b8962e\';return\'#c0392b\';
}

function hmPaint(){
  Object.keys(hmD).forEach(n=>{const e=document.getElementById(\'hm-\'+n);if(e)e.style.fill=hmClr(n,hmM);});
}

function setMetric(m,btn){
  hmM=m;
  document.querySelectorAll(\'.hm-btn\').forEach(b=>{b.style.background=\'transparent\';b.style.color=\'#6b6860\';});
  btn.style.background=\'#c9a84c\'; btn.style.color=\'#0f1014\';
  const lt={yield:\'Rental Yield\',growth:\'5yr Growth\',risk:\'Risk Score\'};
  const lo={yield:\'Low (3%)\',growth:\'Low (2%)\',risk:\'Low Risk\'};
  const hi={yield:\'High (8%+)\',growth:\'High (7%+)\',risk:\'High Risk\'};
  document.getElementById(\'hm-leg-title\').textContent=lt[m];
  document.getElementById(\'hm-leg-lo\').textContent=lo[m];
  document.getElementById(\'hm-leg-hi\').textContent=hi[m];
  document.getElementById(\'hm-rank-title\').textContent=m===\'yield\'?\'Top Counties by Yield\':m===\'growth\'?\'Top Counties by Growth\':\'Lowest Risk Counties\';
  hmPaint(); hmRank(); if(hmS) hmCard(hmS);
}

function hmSel(n){
  document.querySelectorAll(\'.hmc\').forEach(e=>e.classList.remove(\'hm-sel\'));
  const el=document.getElementById(\'hm-\'+n); if(el) el.classList.add(\'hm-sel\');
  hmS=n; hmCard(n);
  document.querySelectorAll(\'.hm-ri\').forEach(i=>i.style.background=i.dataset.c===n?\'#22252a\':\'transparent\');
}

function hmCard(n){
  const d=hmD[n]; if(!d) return;
  const sc=d.signal===\'STRONG BUY\'?\'background:rgba(26,107,60,0.3);color:#4ade80\':
           d.signal===\'MODERATE\'?\'background:rgba(201,168,76,0.2);color:#c9a84c\':
           \'background:rgba(192,57,43,0.2);color:#ef4444\';
  const gc=d.growth>=6?\'#4ade80\':d.growth>=4?\'#c9a84c\':\'#ef4444\';
  const yc=d.yield>=5?\'#4ade80\':d.yield>=4?\'#c9a84c\':\'#ef4444\';
  const rc=d.risk===\'Low\'?\'#4ade80\':d.risk===\'Medium\'?\'#c9a84c\':\'#ef4444\';
  const has=[\'Dublin\',\'Cork\',\'Galway\',\'Kildare\',\'Kerry\',\'Meath\',\'Wicklow\'].includes(n);
  const cta=has
    ?`<a href="/#reports" style="display:block;text-align:center;padding:0.65rem;background:#c9a84c;color:#0f1014;border-radius:3px;font-size:0.72rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;text-decoration:none;margin-top:0.8rem;">Unlock All Micro-Areas in ${n} — €29 →</a>`
    :`<a href="/#snap" style="display:block;text-align:center;padding:0.65rem;background:#1a1c20;color:#9a9690;border:1px solid #2a2c30;border-radius:3px;font-size:0.72rem;font-weight:500;text-decoration:none;margin-top:0.8rem;">Get Free ${n} Snapshot →</a>`;
  document.getElementById(\'hm-info\').innerHTML=`
    <div style="padding:0.9rem 1rem 0.7rem;border-bottom:1px solid #2a2c30;text-align:left;">
      <div style="font-family:\'Playfair Display\',serif;font-size:1.2rem;font-weight:700;color:white;">${n}</div>
      <div style="display:inline-block;font-size:0.6rem;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;padding:0.2rem 0.5rem;border-radius:2px;margin-top:0.3rem;${sc};">${d.signal}</div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;">
      <div style="padding:0.7rem 1rem;border-right:1px solid #2a2c30;border-bottom:1px solid #2a2c30;text-align:left;">
        <div style="font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.2rem;">Gross Yield</div>
        <div style="font-family:\'Playfair Display\',serif;font-size:1.1rem;font-weight:700;color:${yc};">${d.yield}%</div>
      </div>
      <div style="padding:0.7rem 1rem;border-bottom:1px solid #2a2c30;text-align:left;">
        <div style="font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.2rem;">5yr Growth</div>
        <div style="font-family:\'Playfair Display\',serif;font-size:1.1rem;font-weight:700;color:${gc};">+${d.growth}%</div>
      </div>
      <div style="padding:0.7rem 1rem;border-right:1px solid #2a2c30;text-align:left;">
        <div style="font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.2rem;">Risk</div>
        <div style="font-family:\'Playfair Display\',serif;font-size:1.1rem;font-weight:700;color:${rc};">${d.risk}</div>
      </div>
      <div style="padding:0.7rem 1rem;text-align:left;">
        <div style="font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;color:#6b6860;margin-bottom:0.2rem;">Median Price</div>
        <div style="font-family:\'Playfair Display\',serif;font-size:1.1rem;font-weight:700;color:white;">€${d.price.toLocaleString()}</div>
      </div>
    </div>
    ${cta}`;
}

function hmRank(){
  const sorted=Object.entries(hmD).sort((a,b)=>{
    if(hmM===\'yield\') return b[1].yield-a[1].yield;
    if(hmM===\'growth\') return b[1].growth-a[1].growth;
    const r={Low:0,Medium:1,High:2}; return r[a[1].risk]-r[b[1].risk];
  }).slice(0,8);
  document.getElementById(\'hm-rank-list\').innerHTML=sorted.map(([n,d],i)=>{
    const val=hmM===\'yield\'?d.yield+\'%\':hmM===\'growth\'?\'+\'+d.growth+\'%\':d.risk;
    const bw=hmM===\'risk\'?(d.risk===\'Low\'?90:d.risk===\'Medium\'?55:20):(parseFloat(hmM===\'yield\'?d.yield:d.growth)/9*100);
    const bc=hmClr(n,hmM);
    return`<div class="hm-ri" data-c="${n}" onclick="hmSel(\'${n}\')" style="display:flex;align-items:center;gap:0.6rem;padding:0.5rem 1rem;border-bottom:1px solid #2a2c30;cursor:pointer;transition:background 0.12s;">
      <span style="font-size:0.65rem;color:#4a4845;width:14px;">${i+1}</span>
      <span style="font-size:0.8rem;font-weight:500;flex:1;color:white;">${n}</span>
      <div style="width:40px;height:3px;background:#2a2c30;border-radius:2px;overflow:hidden;"><div style="width:${bw}%;height:100%;background:${bc};border-radius:2px;"></div></div>
      <span style="font-size:0.78rem;font-weight:600;color:${bc};min-width:36px;text-align:right;">${val}</span>
    </div>`;
  }).join(\'\');
}

hmPaint(); hmRank();
</script>
<!-- ── END HEATMAP SECTION ── -->'''

new_content = content[:start_idx] + NEW_HEATMAP + content[end_idx:]

with open("app.py", "w", encoding="utf-8") as f:
    f.write(new_content)

# Verify
import ast
try:
    # app.py isn't pure python (has big HTML string), just check markers survived
    assert "<!-- ── HEATMAP SECTION ── -->" in new_content
    assert "<!-- ── END HEATMAP SECTION ── -->" in new_content
    print("✅ Heatmap section replaced successfully!")
    print("Now run:")
    print("  git add app.py")
    print('  git commit -m "Fix heatmap layout - clean rewrite"')
    print("  git push")
except AssertionError:
    print("❌ Something went wrong — markers missing after write")
