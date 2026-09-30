# MJ 提示词整理：机甲 & MGS（合金装备）

> 数据来源：`mj.py list` 接口（`/api/msg/list`），共扫描最近 240 条历史消息，命中机甲类 126 条、MGS 类 41 条。
> 整理时间：2026-09-30。`msg_id` 可用于 `python mj.py get <id>` 回看原图、按钮与 seed。

## 风格速查表

| # | 风格 | 机器人 / 模型 | 固定参数 | 画幅 | 特征关键词 |
|---|------|--------------|---------|------|-----------|
| A | 写实 CG 机甲肖像三连 | `MID_JOURNEY` + `--v 7` | `--ar 3:4` | 3:4 | `octane render`、`brushed metal`、战损战场背景 |
| B | 写实 CG 机甲全身大场景 | `MID_JOURNEY` + `--v 7` | `--s 300 --v 7` | 默认 | `AAA game cinematic CG`、`IMAX movie still`、8K |
| C | 动漫赛璐璐机甲三连 | `NIJI_JOURNEY` + `--niji 7` | `--ar 3:4` | 3:4 | `sharp clean mechanical lineart`、`vibrant cel shading` |
| D | 白底机甲设定图 | `NIJI_JOURNEY` + `--niji 7` | `--ar 3:4` | 3:4 | `plain solid white background`、`clean studio lighting` |
| E | 白底写实人物三连 | `MID_JOURNEY` + `--v 7` | `--ar 3:4 --s 250 --v 7` | 3:4 | `plain solid white background`、`octane render` |
| F | 动漫角色信息卡 | `NIJI_JOURNEY` + `--niji 7` | `--ar 4:5 --s 250 --niji 7` | 4:5 | `character profile card`、`HUD elements`、`cel-shaded` |
| G | 角色设定稿三视图 | `NIJI_JOURNEY` + `--niji 7` | `--ar 4:5` | 4:5 | `character design sheet`、`name plate` |
| H | 头像 avatar | `NIJI_JOURNEY` + `--niji 7` | `--ar 1:1 --s 150~200` | 1:1 | `anime avatar`、`square composition` |

---

## 一、机甲类

### A. 写实 CG 机甲肖像三连（最新，`MID_JOURNEY --v 7`）

同一机体拆成「头部特写 / 上半身 / 全身」三条，是最常用的成套写法。

**A1. EVA 二号机 上半身（2026-09-30 08:14，msg 3233812）**
```
upper body biomechanical mecha of Evangelion Unit-02 from Neon Genesis Evangelion, two prominent horns like a demon mask, smooth featureless face plate with four glowing yellow optic eyes, shoulder armor, chest core unit, weathered metallic and organic armor with deep battle scratches and chipped paint, war-torn battlefield ruins backdrop with swirling smoke, glowing embers and debris, dramatic smoky cinematic war atmosphere, dark moody backdrop, cinematic dramatic lighting, photorealistic brushed metal and organic bio-armor texture, highly detailed realistic cg rendering, octane render --ar 3:4 --v 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/30/merged_eb1e7990db9749bb91c182acb2e8d460.webp?q=9

**A2. EVA 二号机 头部特写（msg 3233655）**
```
close up portrait bust shot of Evangelion Unit-02 from Neon Genesis Evangelion, head and shoulders framing, predominantly crimson red painted armored robot head and shoulder armor with white accent panels, two prominent horns like a demon mask, smooth featureless face plate with four glowing yellow optic eyes, no mouth, subtle dark panel lines for separation, weathered metallic and organic armor with deep battle scratches scuff marks chipped paint and scorch marks, war-torn battlefield ruins backdrop with swirling smoke, glowing embers, scattered mecha debris and broken concrete, dramatic smoky cinematic war atmosphere, dark moody backdrop, cinematic dramatic lighting, photorealistic brushed metal and organic bio-armor texture, highly detailed realistic cg rendering, octane render --ar 3:4 --no full body legs, hud, text, logo, watermark, other robots --v 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/29/merged_3c0b060dd1134603a0bd2e0922c399a7.webp?q=9

**A3. EVA 二号机 全身（msg 3233649）**
```
full body biomechanical mecha of Evangelion Unit-02 from Neon Genesis Evangelion, predominantly crimson red painted armored humanoid with white accent armor panels and details, two prominent horns on head like a demon mask, smooth featureless face plate with four glowing yellow optic eyes, no mouth no facial features, holding a progressive knife, weathered metallic and organic armor with deep battle scratches scuff marks and chipped paint, war-torn battlefield ruins backdrop with swirling smoke, glowing embers, scattered mecha debris and broken concrete, dramatic smoky cinematic war atmosphere, dark moody backdrop, ground shadow on broken concrete, cinematic dramatic lighting, photorealistic brushed metal and organic bio-armor texture, highly detailed realistic cg rendering, octane render --ar 3:4 --no hud, text, logo, watermark, other mecha, other robots --v 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/29/merged_90b387facad84f988596b1786d5d1940.webp?q=9

**A4. EVA 初号机 / 零号机（同一套模板换配色）**
- 初号机：msg 3233646（特写）/ 3233645（上半身）/ 3233644（全身）——`deep violet purple painted ... lime green accent panels, single long horn, a single glowing optic eye`
- 零号机：msg 3233643（特写）/ 3233640（上半身）/ 3233639（全身）——`bright orange painted ... black accent panels and white abdominal segments, single short horn`

**A5. 灾难高达 Calamity GAT-X370 头部特写（2026-09-30 08:04，msg 3233807）**
```
extreme close up head of Calamity Gundam GAT-X370 mobile suit from Gundam SEED Destiny, predominantly dark forest green painted robot head with light green and yellow accent panels, angular horned head crest, green optic visor eye, face vents and black cannon muzzles on cheeks, heavily weathered metallic armor with deep battle scratches and chipped paint, war-torn battlefield background with smoke, embers and debris, dramatic smoky cinematic atmosphere, dark moody backdrop, cinematic dramatic lighting, photorealistic brushed metal texture, highly detailed realistic cg rendering, octane render --ar 3:4 --v 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/30/merged_cabe057111fa41008ef77d504b188765.webp?q=9
（同套：msg 3231897 特写 / 3231891 上半身 / 3231890 全身，全身版武器为 `a large back mounted missile pod ... holding a hyper impulse cannon`）

**A6. 自由高达 Freedom ZGMF-X10A（msg 3232419 特写 / 3232416 上半身 / 3232413 全身）**
```
close up portrait bust shot of Freedom Gundam mobile suit ZGMF-X10A from Gundam SEED, head and shoulders framing, predominantly white painted armored robot head and shoulder armor with blue and red accent panels and yellow detailing, white helmet crest, green optic eyes glowing, face mask vents, subtle gray shading and dark panel lines for separation, heavily weathered metallic armor with deep battle scratches scuff marks chipped paint and scorch marks, war-torn battlefield background with swirling smoke, glowing embers, scattered mecha debris and rubble, dramatic smoky cinematic war atmosphere, dark moody backdrop, cinematic dramatic lighting, photorealistic brushed metal texture, highly detailed realistic cg rendering, octane render --ar 3:4 --no full body legs, hud, text, logo, watermark, other robots --v 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/29/merged_9a969b3fec4042e9924c68d0d283e848.webp?q=9

**A7. ν 高达 RX-93 头部特写（msg 3232411）**
```
close up portrait bust shot of RX-93 Nu Gundam mobile suit from Gundam Char's Counterattack, head and shoulders framing, predominantly white painted armored robot head and shoulder armor with yellow and black accent panels and warning stripes, forward swept V-fin antenna, twin red optic eyes glowing, face mask vents, subtle gray shading and dark panel lines for separation, heavily weathered metallic armor with deep battle scratches scuff marks chipped paint and scorch marks, war-torn battlefield background with swirling smoke, glowing embers, scattered mecha debris and rubble, dramatic smoky cinematic war atmosphere, dark moody backdrop, cinematic dramatic lighting, photorealistic brushed metal texture, highly detailed realistic cg rendering, octane render --ar 3:4 --no full body legs, hud, text, logo, watermark, other robots --v 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/29/merged_732aa998cecd400e990a0bcb98341a91.webp?q=9

---

### B. 写实 CG 机甲全身大场景（`--s 300 --v 7`）

一条提示词塞满材质 + 光照 + 镜头 + 画质词，出「电影海报」级效果。

**B1. ν 高达 沙漠黄昏（msg 3228456）**
```
Nu Gundam RX-93, the legendary white and violet Newtype mobile suit with six fin funnels deployed and hovering around it, heavily battle-damaged after fierce combat, standing on a scorched desert battlefield at dusk, photorealistic AAA game cinematic CG, hyper-realistic 3D render, long range beam rifle, long white and violet armor panels with exposed psycho frame seams, thousands of realistic scratches, deep gouges, chipped and peeled paint, burnt scorch marks, soot, rust streaks, exposed internal frame, torn hydraulic hoses and cables, sand caked into every armor seam, oil stains and dust, volumetric smoke and sandstorm haze, drifting embers and sparks, harsh orange sunset backlight with cold blue fill light, long dramatic shadow, low-angle heroic composition, 24mm anamorphic lens, ray-traced reflections, physically based materials, realistic metal roughness and anisotropic wear, tiny soldiers and wrecked vehicles nearby for epic scale, Hollywood sci-fi blockbuster cinematography, IMAX movie still, ultra detailed, 8K --s 300 --v 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/28/merged_be6bc62324184b97a937789e61bb4f62.webp?q=9

**B2. RX-78-2 元祖高达 废墟黎明（msg 3228455）**
```
RX-78-2 Gundam, the iconic white blue and red mobile suit of the Earth Federation, heavily battle-damaged after fierce combat, standing in the ruins of a devastated industrial city at dawn, photorealistic AAA game cinematic CG, hyper-realistic 3D render, white armor panels with red core block and blue chest vents, beam rifle in right hand and shield on left arm, thousands of realistic scratches, deep gouges, chipped and peeled paint, burnt scorch marks, soot, rust streaks, exposed internal frame, torn hydraulic hoses and cables, mud, oil stains and caked dust, rain-slicked metal surfaces with wet reflections, volumetric smoke and haze, drifting embers and sparks, dramatic cinematic lighting with cold blue dawn light and warm sunrise rim light, low-angle heroic composition, 24mm anamorphic lens, ray-traced reflections, physically based materials, realistic metal roughness and anisotropic wear, tiny soldiers and wrecked vehicles nearby for epic scale, Hollywood sci-fi blockbuster cinematography, IMAX movie still, ultra detailed, 8K --s 300 --v 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/28/merged_4295ff1440384137bae87c6fc4ed4dd2.webp?q=9

**B3. 独角兽高达 毁灭模式（msg 3228457）**
```
Unicorn Gundam in destroy mode, pure white mobile suit split open to reveal a glowing crimson psycho frame all over the body, heavily battle-damaged after fierce combat, standing in a flooded ruined neon city at night in heavy rain, photorealistic AAA game cinematic CG, hyper-realistic 3D render, beam magnum in hand, glowing red inner frame light spilling onto wet debris, thousands of realistic scratches, deep gouges, chipped and peeled paint, burnt scorch marks, soot, rust streaks, exposed internal mechanisms, torn hydraulic hoses and cables, mud, oil stains and caked dust, rain-slicked surfaces with strong wet reflections, volumetric smoke and haze, lightning flash, dramatic cinematic lighting with cold neon blue and hot crimson rim light, low-angle heroic composition, 24mm anamorphic lens, ray-traced reflections, physically based materials, realistic metal roughness and anisotropic wear, tiny soldiers nearby for epic scale, Hollywood sci-fi blockbuster cinematography, IMAX movie still, ultra detailed, 8K --s 300 --v 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/28/merged_a70a01a9dca84d28813164f51441def3.webp?q=9

**B4. 巴巴托斯 铁矿荒地（msg 3228458）**
```
Gundam Barbatos, the rugged close quarters combat frame with a raw exposed internal skeleton and massive iron mace, heavily battle-damaged after brutal melee combat, standing in a dusty iron ore wasteland under harsh midday sun, photorealistic AAA game cinematic CG, hyper-realistic 3D render, dull white and dark grey armor with orange-yellow frame, crude welded plating, thousands of realistic scratches, deep gouges, chipped and peeled paint, burnt scorch marks, soot, rust streaks, torn hydraulic hoses and cables, red iron ore dust caked into every seam, oil stains and grime, swirling sandstorm haze, drifting embers and sparks, brutal hard midday sunlight with strong deep shadows, low-angle heroic composition, 24mm anamorphic lens, ray-traced reflections, physically based materials, realistic metal roughness and anisotropic wear, tiny soldiers and wrecked vehicles nearby for epic scale, Hollywood sci-fi blockbuster cinematography, IMAX movie still, ultra detailed, 8K --s 300 --v 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/28/merged_fc32085b6dad426f893b054937f37d38.webp?q=9

**B5. 受损局部特写（微距镜头）**
- ν 高达 头部微距（msg 3228463）：`Extreme close-up macro shot of the Nu Gundam RX-93 head, ... 100mm macro lens, shallow depth of field, ... ultra detailed micro texture, 8K --s 300 --v 7`
- ν 高达 上半身 / 浮游炮舱（msg 3228464）：`85mm anamorphic lens`、`exposed psycho frame seams glowing faintly violet`
- ν 高达 背部推进器（msg 3228467）：`Close-up from behind ... dramatic cinematic backlight with hot orange rim light`

---

### C. 动漫赛璐璐机甲三连（`NIJI_JOURNEY --niji 7`）

结构与 A 组完全一致，只把结尾渲染词换成：`highly detailed anime mecha illustration, sharp clean mechanical lineart, vibrant cel shading`。

**C1. 自由高达（msg 3232623 特写 / 3232613 上半身 / 3232612 全身）**
```
close up portrait bust shot of ZGMF-X10A Freedom Gundam mobile suit from Gundam SEED head and shoulders, predominantly white painted robot head with blue and red accent panels, forward swept V-fin antenna, twin green optic eyes, face mask vents, battle damaged armor with scratches and chipped paint, war-torn battlefield background with swirling smoke, glowing embers, scattered mecha debris and rubble, dramatic smoky war atmosphere, dark moody backdrop, highly detailed anime mecha illustration, sharp clean mechanical lineart, vibrant cel shading --ar 3:4 --no full body, legs --niji 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/29/merged_b604a0540f5f4a2d82fca384b5011384.webp?q=9

**C2. Hi-ν 高达（msg 3232591 特写 / 3232590 上半身 / 3232586 全身）**
```
full body mecha robot of Hi-nu Gundam mobile suit from Gundam Beltorchika's Children, predominantly white painted armored humanoid combat robot with blue accent panels and thin red yellow detailing, angular head with forward swept V-fin antenna and twin red optic eyes, six large fin funnels mounted in wide wing array on back, holding beam rifle, battle damaged armor with scratches, scuffs and chipped paint, war-torn battlefield background with swirling smoke, glowing embers, scattered mecha debris and rubble, dramatic smoky war atmosphere, dark moody backdrop, highly detailed anime mecha illustration, sharp clean mechanical lineart, vibrant cel shading --ar 3:4 --no hud, text, logo, watermark, other mecha, other robots --niji 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/29/merged_6d89e527cbb54b788d3012cc1d5b0271.webp?q=9

**C3. ν 高达（msg 3232581 / 3232576 / 3232575）**：`yellow and black accent panels`、`twin red optic eyes`、`fin funnels mounted on back`

**C4. 灾难高达（msg 3232611 / 3232603 / 3232601）**：`massively built bulky heavy artillery combat robot`、`large shoulder mounted cannons and back missile pods`、`single red optic eye`

**C5. EVA × 主角同框主视觉（msg 3222495）**
```
EVA Unit-01 and EVA Unit-02 standing behind the protagonists as colossal towering mecha, Unit-01 in purple and neon green with horned helmet, Unit-02 in red and white with twin horn crest, foreground Shinji Ikari and Asuka Langley Soryu back to back in plugsuits, Shinji in white plugsuit with blue trim, Asuka in red plugsuit, both looking forward with determined expressions, camera at hip level shooting upward, ultra wide angle lens, blue sky with puffy cumulus clouds, Rebuild of Evangelion movie style, modern theatrical anime film --ar 4:5 --niji 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/27/merged_efd147ab64fb4f7391d7ad619a6b3b7b.webp?q=9

---

### D. 白底机甲设定图（`--niji 7` + 纯白背景）

背景换成 `plain solid white background, clean studio lighting`，并用 `--no scenery, landscape, outdoor...` 兜底。

**D1. VF-1S 女武神（Macross）头部（msg 3230892）**
```
close up head of VF-1S Valkyrie Skull Squadron Battroid mecha from Macross, red and white painted robot head, white skull emblem visor, goggle eyes, antenna sensor, plain solid white background, clean studio lighting, highly detailed anime mecha illustration, sharp clean lines --ar 3:4 --no full body, body, scenery, landscape, outdoor, text, logo, watermark, other robots --niji 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/29/merged_c403833944564235b3d19158494aeb04.webp?q=9

**D2. VF-1S 全身（msg 3230890）**
```
full body mecha robot of VF-1S Valkyrie Skull Squadron Battroid mode from Macross, red and white painted armored humanoid combat robot, white skull emblem on head visor, shoulder missile pods, holding GU-11 rifle, plain solid white background, clean studio lighting, subtle soft ground shadow, highly detailed anime mecha illustration, sharp clean lines --ar 3:4 --no scenery, landscape, outdoor, hud, text, logo, watermark, other mecha, other robots --niji 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/29/merged_9988fb0b4f6e456db23e9f45b83e4174.webp?q=9

---

## 二、MGS / 合金装备类

### E. 白底写实人物三连（`MID_JOURNEY --v 7 --ar 3:4 --s 250`）

模板结构：
`{景别} of {角色} from {作品}, {外貌}, {服装装备}, {表情}, plain solid white background, clean studio lighting, {阴影}, highly detailed realistic cg rendering, octane render --ar 3:4 --no scenery, landscape, outdoor, hud, text, logo, watermark, {排除项} --s 250 --v 7`

**E1. Solid Snake 全身（msg 3229970）**
```
full body character portrait of Solid Snake from Metal Gear Solid, black short hair, black tactical military combat outfit with chest harness and pouches, black headband, stubble beard, tactical eyewear, confident calm expression, three-quarter view pose, plain solid white background, clean studio lighting, subtle soft ground shadow, highly detailed realistic cg rendering, octane render --ar 3:4 --no scenery, landscape, outdoor, hud, text, logo, watermark, other people --s 250 --v 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/29/merged_5cf9a8e150a7470ca1017dc0b0bee9a4.webp?q=9

**E2. Solid Snake 上半身（msg 3229973）**
```
upper body portrait waist up of Solid Snake from Metal Gear Solid, black short hair, black tactical military combat outfit with chest harness and pouches, black headband, stubble beard, tactical eyewear, confident expression, three-quarter view, plain solid white background, clean studio lighting, subtle soft shadow, highly detailed realistic cg rendering, octane render --ar 3:4 --no scenery, landscape, outdoor, hud, text, logo, watermark, full body, legs, rifle --s 250 --v 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/29/merged_1d3a056de656494d90029337364af535.webp?q=9

**E3. Solid Snake 面部特写（msg 3229974）**
```
face close-up portrait of Solid Snake from Metal Gear Solid, black short hair, black headband, stubble beard, tactical eyewear, confident calm eyes, plain solid white background, clean studio lighting, highly detailed realistic cg rendering, octane render --ar 3:4 --no scenery, landscape, outdoor, hud, text, logo, watermark, full body, body, combat outfit --s 250 --v 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/29/merged_4442cba1709042b1b473f02ed5f12ad4.webp?q=9

**E4. MGS3 角色群（同一模板批量替换，都是这套三连）**

| 角色 | 面部特写 | 上半身 | 全身 | 关键外貌 / 装备词 |
|------|---------|--------|------|------------------|
| Naked Snake | 3228811 | 3228806 | 3228736 | `green bandana headband`、`Mosin Nagant sniper rifle`、`jungle rucksack` |
| The Boss | 3229662 | 3229657 | 3229645 | `short silver white hair`、`green headband`、`Patriot rifle`、`long cape` |
| Revolver Ocelot | 3229688 | 3229678 | 3229668 | `slick dark brown hair`、`arrogant smirk`、`twin revolvers` |
| EVA (Tatyana) | 3229845 | 3229843 | 3229837 | `long dark hair`、`black leather aviation flight suit`、`pistol` |
| Colonel Volgin | 3229854 | 3229849 | 3229847 | `bald head with burn scar`、`Soviet uniform`、`electric sparks` |
| The End | 3229912 | 3229905 | 3229903 | `extremely elderly frail sniper`、`ghillie net`、`wheelchair` |
| The Sorrow | 3229926 | 3229922 | 3229919 | `pale ghostly translucent`、`wet hair`、`ethereal pale glow` |
| Major Zero | 3229935 | 3229934 | 3229929 | `round rimmed glasses`、`balding`、`tobacco pipe` |

**E5. Naked Snake 全身（写实版，msg 3228736）**
```
full body character portrait of Naked Snake from Metal Gear Solid 3 Snake Eater, young man with short stubble beard and green bandana headband, olive green military tactical vest with ammo pouches, large jungle rucksack backpack, Mosin Nagant sniper rifle slung across back, survival knife on chest, silver dog tags, olive cargo pants with knee pads, brown combat boots, earpiece radio headset, confident calm expression, three-quarter view pose, plain solid white background, clean studio lighting, subtle soft ground shadow, highly detailed realistic cg rendering, octane render --ar 3:4 --no scenery, landscape, outdoor, hud, text, logo, watermark, camo face paint --s 250 --v 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/29/merged_cba6aa881bdf48e0a1e7bf9e96bfc5c3.webp?q=9

**E6. Naked Snake 全身（niji 7 赛璐璐版，msg 3228735）**
与 E5 完全同结构，仅把 `highly detailed realistic cg rendering, octane render` 换成 `cel-shaded anime illustration with clean linework`，模型换 `--niji 7`。
> 这是「写实 ↔ 动漫」切换的最小改动写法：只改渲染词 + 模型参数。

---

### F. 动漫角色信息卡（`NIJI_JOURNEY --niji 7 --ar 4:5 --s 250`）

模板：
`anime style character profile card illustration of {角色} from Metal Gear Solid, {外貌}, {服装}, {动作/道具}, dark industrial tactical espionage background with subtle tactical map grid and red laser lines, neon green holographic HUD elements floating around, character info text placeholder areas at top and bottom, cel-shaded anime illustration, sharp clean lines, dramatic cinematic lighting, {配色} color palette --ar 4:5 --s 250 --niji 7`

**F1. Solid Snake（msg 3226197）**
```
anime style character profile card illustration of Solid Snake from Metal Gear Solid, rugged middle-aged special forces operative with short blonde hair and infinity bandana, stern blue eyes, scarred square jaw with stubble beard, wearing iconic grey sneaking suit with high collar and chest harness with ammo pouches, holding a suppressed pistol in one hand and crouching beside his iconic cardboard box disguise, dark industrial tactical espionage background with subtle tactical map grid and red laser lines, neon green holographic HUD elements floating around him, character info text placeholder areas at top and bottom, cel-shaded anime illustration, sharp clean lines, dramatic cinematic lighting, cool cyan and grey color palette --ar 4:5 --s 250 --niji 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/28/merged_dc44f52b6f864c6e8c8526187ec2c142.webp?q=9

**F2. Revolver Ocelot（msg 3226477）**
```
anime style character profile card illustration of Revolver Ocelot from Metal Gear Solid, lean gunslinger with slicked-back grey hair and thin mustache, sly confident grin, wearing a long red leather duster coat and black gloves, twin single-action revolvers on holsters, performing his signature revolver-spinning flourish, dark industrial tactical espionage background with subtle tactical map grid and red laser lines, neon green holographic HUD elements floating around, character info text placeholder areas at top and bottom, cel-shaded anime illustration, sharp clean lines, dramatic cinematic lighting, crimson red and dark brown color palette --ar 4:5 --s 250 --niji 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/28/merged_34e48965e2534d7e97ae578541bbc31d.webp?q=9

**F3. The Boss（msg 3226492）**
```
anime style character profile card illustration of The Boss from Metal Gear Solid, dignified legendary female soldier in her forties with long blonde hair tied back and a scarred mature face, calm commanding expression, wearing a white tactical sneaking suit with chest holster, holding the Patriot assault rifle with its distinctive drum belt feed, dark industrial tactical espionage background with subtle tactical map grid and red laser lines, neon green holographic HUD elements floating around, character info text placeholder areas at top and bottom, cel-shaded anime illustration, sharp clean lines, dramatic cinematic lighting, white and gold color palette --ar 4:5 --s 250 --niji 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/28/merged_42128ca3164246119a5096768030efd3.webp?q=9

**F4. Meryl Silverburgh（msg 3226501）**
```
anime style character profile card illustration of Meryl Silverburgh from Metal Gear Solid, young red-haired female soldier with green eyes and a determined expression, wearing a green tank top under a tactical vest and desert camouflage cargo pants, holding a large Desert Eagle pistol in both hands, dark industrial tactical espionage background with subtle tactical map grid and red laser lines, neon green holographic HUD elements floating around, character info text placeholder areas at top and bottom, cel-shaded anime illustration, sharp clean lines, dramatic cinematic lighting, olive green and warm orange color palette --ar 4:5 --s 250 --niji 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/28/merged_4eea3d781f134d80b088638e7b4e4bf2.webp?q=9

**F5. Raiden（msg 3226533）**
```
anime style character profile card illustration of Raiden from Metal Gear Solid, handsome young cyber ninja soldier with chin-length platinum white hair and blue eyes, wearing a sleek black high-tech exoskeleton suit with glowing electric blue circuit lines and harness straps, holding a glowing high-frequency katana in an elegant fencing stance, dark industrial tactical espionage background with subtle tactical map grid and red laser lines, neon green holographic HUD elements floating around, character info text placeholder areas at top and bottom, cel-shaded anime illustration, sharp clean lines, dramatic cinematic lighting, white and electric blue color palette --ar 4:5 --s 250 --niji 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/28/merged_74f3a6001c194fb085db0a98210a6e90.webp?q=9

**F6. 中文写法的同一张卡（最新，msg 3233808；变体 3233814）**
```
漂亮的人物信息卡，白色背景，合金装备3，solid snake, full body,upper body,face,weapon,equipment,8k,ultra detailed --ar 4:5 --niji 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/30/merged_5ada2c4003354f8395a665b697a197db.webp?q=9
> 服务端实际生效提示词会补 `--stylize 100`：
> `漂亮的人物信息卡，白色背景，合金装备3，solid snake, full body,upper body,face,weapon,equipment,8k,ultra detailed --ar 4:5 --stylize 100 --niji 7`

---

### G. 角色设定稿 / 三视图（`character design sheet`）

模板：
`{角色} character design sheet, Yoji Shinkawa design, Hideo Kojima cinematic direction, niji 7, upper body portrait from chest up, {细节}, clean white background, name plate "{角色}" at the bottom, front view with small side and back head shots on the right, cel shading, clean lineart, flat colors --ar 4:5 --niji 7`

**G1. Solid Snake（msg 3219195）**
```
Solid Snake character design sheet, Yoji Shinkawa design, Hideo Kojima cinematic direction, niji 7, upper body portrait from chest up, Solid Snake from Metal Gear Solid, short dark brown hair with side part, square jaw, intense blue eyes, black sneaking suit printed with pixelated desert pattern, olive drab ballistic vest over the suit, balaclava pulled down around the neck, tactical belt with radio pouch and M9 holster, thigh rig, sneaking indicator HUD light faintly glowing on the chest rig, cold breath visible in the air, clean white background, name plate "Solid Snake" at the bottom, front view with small side and back head shots on the right, cel shading, clean lineart, flat tactical colors with subtle shading --ar 4:5 --niji 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/26/merged_152f3637e0144d7c9fc40dad3f922cf3.webp?q=9

**G2. Solid Snake（简化版，msg 3219187）**
```
Solid Snake character design sheet, niji 7, upper body portrait from chest up, short dark brown hair with side part, thick square jaw, intense blue eyes, faint beard stubble, black tactical sneaking suit with integrated harness, olive drab ballistic vest over the suit, black balaclava pulled down around the neck, tactical belt with pouches and holster, thigh rig with pistol, fingerless gloves, stoic expression, clean white background, name plate "Solid Snake" at the bottom, front view with small side-view and back-view head shots on the right, cel shading, clean lineart, flat tactical colors with subtle shading --ar 4:5 --niji 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/26/merged_455538feab944b3fbc07e8f303d1b564.webp?q=9

**G3. Venom Snake（msg 3222574）**
```
Venom Snake character design sheet, Yoji Shinkawa design, Hideo Kojima cinematic direction, niji 7, upper body portrait from chest up, weathered rugged face, grey stubble beard, missing right eye covered by an eye patch, facial scar across the forehead, black bandana with frayed edges wrapped around the head, brown leather tactical jacket with fur-lined collar, olive drab pants, chest rig with smoke grenade and ammo pouches, right hand replaced by a metal prosthetic bionic hook, fingerless gloves, intense gaze, clean white background, name plate "Venom Snake" at the bottom, front view with small side and back head shots on the right, cel shading, clean lineart, flat colors --ar 4:5 --niji 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/27/merged_0c5c398fd9b74e53b0b5482b4a0165ba.webp?q=9

---

### H. 头像 / avatar（`--ar 1:1`）

**H1. 动漫头像（msg 3223005）**
```
anime avatar, cel shaded 2D animation style, flat colors, bold clean outlines, rugged male soldier in desert camouflage uniform with tactical vest, bandana, stubble beard, intense determined gaze, holding a compact submachine gun, Metal Gear Solid inspired hard-boiled action hero, clean lineart, muted sandy palette, simple background, square portrait composition --ar 1:1 --s 150 --niji 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/27/merged_426322492a6d4222880ea0c9346882a3.webp?q=9

**H2. 写实 CGI 头像（msg 3222996）**
```
character portrait avatar, rugged male soldier, military camouflage uniform with tactical vest, bandana, stubble beard, intense determined gaze, holding a compact submachine gun, dramatic cinematic lighting, dark moody background, Final Fantasy VII Remake realistic CGI rendering, Metal Gear Solid style hard-boiled atmosphere, hyper-detailed, upper body, square composition --ar 1:1 --s 200 --niji 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/27/merged_9b00b1f7b3d34f7697d4beaa5e28e90a.webp?q=9

---

### I. Metal Gear REX 机体场景（写实，`--s 300 --v 7`）

**I1. REX 战损全景（msg 3228453）**
```
Metal Gear REX bipedal nuclear walking battle tank from Metal Gear Solid, heavily battle-damaged war machine in the ruins of a devastated military base, photorealistic AAA game cinematic CG, hyper-realistic 3D render, massive armored legs, twin railgun arms, cockpit pod, angular welded steel armor plates with visible casting grain and panel seams, thousands of realistic scratches, deep gouges, chipped and peeled paint, burnt scorch marks, soot, rust streaks, exposed hydraulic pistons, torn cables and internal mechanics, mud, oil stains and caked dust, rain-slicked metal surfaces, wet reflections, volumetric smoke and haze, drifting embers and sparks, dramatic cinematic lighting with cold blue moonlight and warm orange muzzle-flash rim light, low-angle heroic composition, 24mm anamorphic lens, ray-traced reflections, physically based materials, realistic metal roughness and anisotropic wear, tiny soldiers nearby for epic scale, Hollywood sci-fi blockbuster cinematography, IMAX movie still, ultra detailed, 8K --s 300 --v 7
```
图：https://cdn.aitoptop.cn/attachments/merges/2026/09/28/merged_5c7b58d0fa55472bb7de10bc66e24c2f.webp?q=9

---

## 三、可复用填空模板

### 1. 写实机甲肖像三连（`MID_JOURNEY --v 7`）
```
{close up portrait bust shot|upper body|full body} {mecha|biomechanical mecha|mecha robot} of {机体名} from {作品}, {主色 painted} armored {head|torso|humanoid} with {配色 accent panels}, {头部特征: horns / V-fin antenna / crest}, {眼睛: optic eyes / visor}, {胸口/肩甲细节}, weathered metallic armor with deep battle scratches scuff marks chipped paint and scorch marks, war-torn battlefield ruins backdrop with swirling smoke, glowing embers, scattered mecha debris and broken concrete, dramatic smoky cinematic war atmosphere, dark moody backdrop, cinematic dramatic lighting, photorealistic brushed metal texture, highly detailed realistic cg rendering, octane render --ar 3:4 --no hud, text, logo, watermark, other mecha, other robots --v 7
```

### 2. 动漫机甲三连（`NIJI_JOURNEY --niji 7`）
```
{close up portrait bust shot|upper body|full body} mecha robot of {机体名} from {作品}, {配色描述}, battle damaged armor with scratches and chipped paint, war-torn battlefield background with swirling smoke, glowing embers, scattered mecha debris and rubble, dramatic smoky war atmosphere, dark moody backdrop, highly detailed anime mecha illustration, sharp clean mechanical lineart, vibrant cel shading --ar 3:4 --no hud, text, logo, watermark, other mecha, other robots --niji 7
```

### 3. 写实 MGS 人物三连（`MID_JOURNEY --v 7`）
```
{face close-up portrait|upper body portrait waist up|full body character portrait} of {角色} from Metal Gear Solid {作品副标题}, {发型/五官}, {服装}, {道具}, {表情}, {视角}, plain solid white background, clean studio lighting, {subtle soft shadow / subtle soft ground shadow}, highly detailed realistic cg rendering, octane render --ar 3:4 --no scenery, landscape, outdoor, hud, text, logo, watermark, {排除项} --s 250 --v 7
```

### 4. 动漫角色信息卡（`NIJI_JOURNEY --niji 7`）
```
anime style character profile card illustration of {角色} from Metal Gear Solid, {外貌}, {服装}, {动作/道具}, dark industrial tactical espionage background with subtle tactical map grid and red laser lines, neon green holographic HUD elements floating around, character info text placeholder areas at top and bottom, cel-shaded anime illustration, sharp clean lines, dramatic cinematic lighting, {配色} color palette --ar 4:5 --s 250 --niji 7
```

---

## 四、生成命令备忘

```bash
# 写实机甲（MJ v7）
python .codebuddy/skills/mj-client/scripts/mj.py imagine "<prompt>" --type MID_JOURNEY --model "--v 7" --ar 3:4 --speed fast --wait

# 动漫机甲 / MGS 信息卡（niji 7）
python .codebuddy/skills/mj-client/scripts/mj.py imagine "<prompt>" --type NIJI_JOURNEY --model "--niji 7" --ar 4:5 --stylize 250 --speed fast --wait

# 回看原图 / 取 seed / 放大
python .codebuddy/skills/mj-client/scripts/mj.py get <msg_id>
python .codebuddy/skills/mj-client/scripts/mj.py seed --msg-id <msg_id>
python .codebuddy/skills/mj-client/scripts/mj.py action <msg_id> U1 --wait
```

> 提醒：`--type` 必须与被操作消息的 `type` 一致；`action`/`modal`/`seed` 会自动沿用消息自带的 type。
> 写实向必须显式 `--model "--v 7"`，否则会沿用账号默认的 `--niji 7`。


