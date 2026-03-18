"""
fix_all_counties.py
Complete fix of all county shapes - proper sizes and no black NI blob
Run from: C:\\Users\\WAFI\\irish-property-insights
"""
import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace the entire SVG content between the svg tags
old_svg_start = '<svg id="hm-svg" viewBox="18 12 255 270"'
new_svg = '''<svg id="hm-svg" viewBox="0 0 400 440" xmlns="http://www.w3.org/2000/svg" style="width:100%;display:block;">
          <!-- DONEGAL - large, northwest -->
          <path id="hm-Donegal"   onclick="hmSel('Donegal')"   class="hmc" d="M60,20 L130,10 L165,25 L175,50 L155,70 L135,85 L105,78 L75,58 L55,40 Z"/>
          <!-- MAYO - large, west -->
          <path id="hm-Mayo"      onclick="hmSel('Mayo')"      class="hmc" d="M20,90 L65,78 L90,72 L100,95 L85,115 L70,110 L55,130 L28,138 L12,120 L18,102 Z"/>
          <!-- SLIGO - small, northwest -->
          <path id="hm-Sligo"     onclick="hmSel('Sligo')"     class="hmc" d="M80,78 L110,72 L125,82 L128,98 L110,108 L88,106 L72,94 Z"/>
          <!-- LEITRIM - medium -->
          <path id="hm-Leitrim"   onclick="hmSel('Leitrim')"   class="hmc" d="M125,72 L148,68 L160,80 L158,100 L142,110 L128,108 L125,95 Z"/>
          <!-- DONEGAL label fix - already done above -->
          <!-- CAVAN - medium, north midlands -->
          <path id="hm-Cavan"     onclick="hmSel('Cavan')"     class="hmc" d="M158,72 L188,65 L205,75 L205,95 L188,103 L168,100 L158,88 Z"/>
          <!-- MONAGHAN - medium -->
          <path id="hm-Monaghan"  onclick="hmSel('Monaghan')"  class="hmc" d="M205,68 L232,62 L248,75 L242,92 L220,96 L205,88 Z"/>
          <!-- LOUTH - small, east -->
          <path id="hm-Louth"     onclick="hmSel('Louth')"     class="hmc" d="M242,75 L265,70 L275,88 L265,105 L245,105 L235,92 Z"/>
          <!-- ROSCOMMON - medium, midlands -->
          <path id="hm-Roscommon" onclick="hmSel('Roscommon')" class="hmc" d="M100,115 L128,108 L145,118 L142,140 L125,150 L105,148 L92,135 Z"/>
          <!-- LONGFORD - medium -->
          <path id="hm-Longford"  onclick="hmSel('Longford')"  class="hmc" d="M148,100 L172,96 L182,108 L178,125 L160,130 L145,122 Z"/>
          <!-- WESTMEATH - medium -->
          <path id="hm-Westmeath" onclick="hmSel('Westmeath')" class="hmc" d="M172,96 L200,92 L215,105 L212,122 L192,128 L175,122 L178,108 Z"/>
          <!-- MEATH - medium, east midlands -->
          <path id="hm-Meath"     onclick="hmSel('Meath')"     class="hmc" d="M205,95 L235,92 L252,105 L248,128 L225,135 L205,128 L205,108 Z"/>
          <!-- DUBLIN - larger, east coast -->
          <path id="hm-Dublin"    onclick="hmSel('Dublin')"    class="hmc" d="M252,105 L278,100 L292,118 L285,140 L262,145 L248,132 Z"/>
          <!-- GALWAY - large, west -->
          <path id="hm-Galway"    onclick="hmSel('Galway')"    class="hmc" d="M18,148 L55,138 L82,128 L95,140 L92,162 L75,178 L50,180 L22,168 Z"/>
          <!-- OFFALY - medium -->
          <path id="hm-Offaly"    onclick="hmSel('Offaly')"    class="hmc" d="M148,130 L178,125 L192,138 L188,155 L165,160 L148,152 Z"/>
          <!-- KILDARE - medium, east -->
          <path id="hm-Kildare"   onclick="hmSel('Kildare')"   class="hmc" d="M212,128 L242,125 L255,142 L248,162 L225,165 L210,152 Z"/>
          <!-- WICKLOW - medium, southeast -->
          <path id="hm-Wicklow"   onclick="hmSel('Wicklow')"   class="hmc" d="M262,145 L288,140 L302,158 L295,180 L272,188 L255,175 L255,158 Z"/>
          <!-- LAOIS - medium -->
          <path id="hm-Laois"     onclick="hmSel('Laois')"     class="hmc" d="M175,158 L205,152 L218,165 L212,182 L190,188 L172,180 Z"/>
          <!-- CLARE - medium, west -->
          <path id="hm-Clare"     onclick="hmSel('Clare')"     class="hmc" d="M52,185 L80,178 L95,165 L108,175 L112,192 L100,208 L78,215 L55,205 Z"/>
          <!-- TIPPERARY - large, south midlands -->
          <path id="hm-Tipperary" onclick="hmSel('Tipperary')" class="hmc" d="M108,175 L138,168 L162,172 L175,188 L168,210 L148,218 L125,215 L108,202 Z"/>
          <!-- CARLOW - small -->
          <path id="hm-Carlow"    onclick="hmSel('Carlow')"    class="hmc" d="M212,182 L235,178 L245,192 L238,208 L218,210 L208,196 Z"/>
          <!-- KILKENNY - medium -->
          <path id="hm-Kilkenny"  onclick="hmSel('Kilkenny')"  class="hmc" d="M175,205 L205,198 L222,210 L218,230 L198,238 L175,230 Z"/>
          <!-- LIMERICK - medium, southwest -->
          <path id="hm-Limerick"  onclick="hmSel('Limerick')"  class="hmc" d="M78,225 L108,215 L128,218 L138,235 L128,252 L105,258 L80,248 L70,235 Z"/>
          <!-- WATERFORD - medium -->
          <path id="hm-Waterford" onclick="hmSel('Waterford')" class="hmc" d="M148,222 L178,215 L200,220 L205,238 L188,252 L162,255 L145,242 Z"/>
          <!-- WEXFORD - medium, southeast -->
          <path id="hm-Wexford"   onclick="hmSel('Wexford')"   class="hmc" d="M205,235 L232,228 L248,242 L245,265 L222,272 L200,260 L198,242 Z"/>
          <!-- KERRY - large, southwest -->
          <path id="hm-Kerry"     onclick="hmSel('Kerry')"     class="hmc" d="M38,255 L70,248 L80,265 L75,290 L55,305 L32,302 L18,280 L25,262 Z"/>
          <!-- CORK - largest, south -->
          <path id="hm-Cork"      onclick="hmSel('Cork')"      class="hmc" d="M80,262 L115,255 L148,258 L165,268 L168,288 L155,305 L125,315 L95,312 L70,298 L68,278 Z"/>

          <!-- LABELS -->
          <text x="108" y="48"  font-size="9"   fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none" font-weight="500">Donegal</text>
          <text x="52"  y="112" font-size="8.5" fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none" font-weight="500">Mayo</text>
          <text x="100" y="94"  font-size="7.5" fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Sligo</text>
          <text x="142" y="92"  font-size="7"   fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Leitrim</text>
          <text x="182" y="88"  font-size="7.5" fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Cavan</text>
          <text x="224" y="83"  font-size="7.5" fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Monaghan</text>
          <text x="255" y="91"  font-size="7.5" fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Louth</text>
          <text x="118" y="133" font-size="7.5" fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Roscommon</text>
          <text x="162" y="117" font-size="7"   fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Longford</text>
          <text x="194" y="113" font-size="7.5" fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Westmeath</text>
          <text x="228" y="115" font-size="8"   fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Meath</text>
          <text x="268" y="125" font-size="8"   fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Dublin</text>
          <text x="55"  y="158" font-size="8.5" fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Galway</text>
          <text x="168" y="146" font-size="7.5" fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Offaly</text>
          <text x="232" y="148" font-size="7.5" fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Kildare</text>
          <text x="278" y="165" font-size="7.5" fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Wicklow</text>
          <text x="194" y="172" font-size="7.5" fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Laois</text>
          <text x="82"  y="198" font-size="8"   fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Clare</text>
          <text x="140" y="196" font-size="8"   fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Tipperary</text>
          <text x="228" y="197" font-size="7"   fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Carlow</text>
          <text x="198" y="218" font-size="7.5" fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Kilkenny</text>
          <text x="105" y="238" font-size="8"   fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Limerick</text>
          <text x="176" y="237" font-size="7.5" fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Waterford</text>
          <text x="222" y="252" font-size="7.5" fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Wexford</text>
          <text x="48"  y="278" font-size="8.5" fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Kerry</text>
          <text x="120" y="285" font-size="9"   fill="rgba(255,255,255,0.7)" text-anchor="middle" pointer-events="none">Cork</text>
        </svg>'''

# Find and replace the entire SVG
svg_pattern = r'<svg id="hm-svg"[^>]*>.*?</svg>'
match = re.search(svg_pattern, content, re.DOTALL)
if match:
    content = content[:match.start()] + new_svg + content[match.end():]
    print("✅ Replaced entire SVG with fixed county shapes")
else:
    print("❌ Could not find SVG to replace")
    # Try simpler approach
    if old_svg_start in content:
        print("Found SVG start, trying alternative replacement...")

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("\nNow run:")
print("  git add app.py")
print("  git commit -m \"Fix all county sizes and remove NI blob\"")
print("  git push")
