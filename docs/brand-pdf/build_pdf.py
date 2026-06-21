#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сборка бренд-платформы «Мама рядом» в PDF (§7).

Что делает: берёт брендовые шрифты и логотип из docs/brand-assets/, встраивает их в
HTML как base64, наполняет шаблон текстом платформы (простым языком, для людей) и
сохраняет готовый HTML. Дальше его рендерит в PDF Chrome (--headless --print-to-pdf).

Только стандартная библиотека — никаких внешних зависимостей.
Запуск:  python3 docs/brand-pdf/build_pdf.py
Потом:   Chrome --headless --print-to-pdf (см. соседний шаг сборки).
"""
import base64
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "brand-assets" / "Мама рядом Бренд"
OUT_HTML = ROOT / "docs" / "brand-pdf" / "brand-platform.html"


def b64(path: pathlib.Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def font_face(family: str, file: str, weight: str = "normal", style: str = "normal") -> str:
    data = b64(ASSETS / "Шрифты" / file)
    return (
        "@font-face{font-family:'%s';font-weight:%s;font-style:%s;"
        "src:url(data:font/ttf;base64,%s) format('truetype');}"
        % (family, weight, style, data)
    )


# --- шрифты ---
FONTS = "".join([
    font_face("Neucha", "Акцентный/Neucha.ttf"),
    font_face("Nunito", "Основной/NunitoSans-Light.ttf", "300"),
    font_face("Nunito", "Основной/NunitoSans-Regular.ttf", "400"),
    font_face("Nunito", "Основной/NunitoSans-Bold.ttf", "700"),
    font_face("Nunito", "Основной/NunitoSans-ExtraBold.ttf", "800"),
])

LOGO = b64(ASSETS / "Логотип" / "Цвет" / "Лого_1.png")

# --- декоративные элементы (настоящие из брендбука) ---
HEART = ('<svg viewBox="0 0 211 197" xmlns="http://www.w3.org/2000/svg"><path d="M209.854 43.8795C220.365 96.2927 137.359 167.733 97.1565 196.808C80.5152 179.682 41.7792 138.64 19.9655 111.479C-7.30159 77.5283 -9.63367 20.668 31.8383 2.76877C65.0158 -11.5506 91.5365 33.1414 100.65 57.2773C105.71 46.7936 118.663 23.3589 129.997 13.4891C144.163 1.1519 197.6 -17.2276 209.854 43.8795Z" fill="#FFF7B0"/></svg>')
FLOWER = ('<svg viewBox="0 0 228 242" xmlns="http://www.w3.org/2000/svg"><path d="M137.307 1.26664C106.912 -9.181 97.7322 47.5686 96.9418 77.2494C76.7598 23.8239 18.5854 29.7602 1.96418 70.1261C-14.6571 110.492 80.3188 133.049 57.7614 130.675C35.204 128.3 -13.4724 161.543 9.08496 201.909C31.6424 242.275 96.9418 149.671 87.4449 168.666C77.948 187.662 108.815 264.832 144.432 233.964C172.926 209.27 151.554 167.479 137.307 149.671C145.618 156.003 169.601 168.666 199.045 168.666C235.849 168.666 232.287 128.3 216.853 102.181C204.506 81.2861 163.428 93.475 144.432 102.181C146.015 97.8282 151.793 85.3226 162.241 70.1261C175.3 51.1304 175.3 14.3262 137.307 1.26664Z" fill="#FFE5D1"/><circle cx="107.344" cy="123.166" r="23.4261" fill="#FFF7B0"/></svg>')
CLOUD = ('<svg viewBox="0 0 224 171" xmlns="http://www.w3.org/2000/svg"><path d="M95.0658 0.748131C88.0898 -0.393416 82.0832 -0.181321 76.9248 1.06292C37.4622 10.5816 19.9716 69.567 4.81036 107.224C-0.735901 120.999 -2.31698 135.953 4.5511 149.953C29.0466 199.886 74.3418 144.895 114.854 136.416C155.365 127.936 154.423 144.895 192.109 118.515C229.794 92.1352 242.274 27.4883 177.034 36.5493C143.118 41.26 146.883 9.22734 95.0658 0.748131Z" fill="#CFE1FF"/></svg>')

CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family:'Nunito',sans-serif; color:#546A88; font-size:13.5pt; line-height:1.72; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
.page { width:210mm; height:297mm; padding:22mm 22mm; position:relative; overflow:hidden; page-break-after:always; display:flex; flex-direction:column; }
.page:last-child { page-break-after:auto; }
.sec-body { display:flex; flex-direction:column; justify-content:center; flex:1; }
h1,h2,h3 { font-family:'Neucha',cursive; font-weight:400; color:#7393CC; line-height:1.1; }
p { margin-bottom:14px; }
b,strong { font-weight:800; color:#3f5675; }
.accent-yellow { color:#3f5675; background:#FFF7B0; padding:0 4px; border-radius:4px; }

/* --- обложка --- */
.cover { background:#7393CC; color:#fff; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; }
.cover .logobox { background:#fff; border-radius:32px; padding:40px; box-shadow:0 16px 44px rgba(40,55,90,.18); width:128mm; display:flex; align-items:center; justify-content:center; }
.cover img { width:96mm; display:block; margin:0 auto; }
.cover .kicker { font-family:'Nunito'; font-weight:800; letter-spacing:.32em; text-transform:uppercase; font-size:12pt; margin-top:54px; opacity:.92; }
.cover .title { font-family:'Neucha'; color:#fff; font-size:56pt; margin-top:6px; }
.cover .sub { font-family:'Neucha'; color:#FFF7B0; font-size:24pt; margin-top:4px; }
.cover .for { margin-top:44px; font-size:11pt; opacity:.85; max-width:120mm; }

/* --- секции --- */
.sec-num { font-family:'Neucha'; font-size:24pt; color:#CFE1FF; }
h2.sec { font-size:42pt; margin:2px 0 20px; }
.lead { font-size:15.5pt; color:#5d7characters; margin-bottom:8px; }
.statement { font-family:'Neucha'; font-size:32pt; color:#7393CC; background:#F4F8FF; border-left:9px solid #FFF7B0; border-radius:0 18px 18px 0; padding:26px 30px; margin:14px 0 22px; line-height:1.22; }

/* врезка-пояснение (напр. «что такое позиционирование») */
.define { background:#EAF1FB; border-radius:18px; padding:18px 24px; font-size:12.5pt; line-height:1.6; margin:8px 0 16px; }
.define .lab { font-family:'Neucha'; font-size:16pt; color:#7393CC; display:block; margin-bottom:5px; }
.connector { font-weight:800; color:#3f5675; font-size:14pt; margin-bottom:0; }
h3.subsec { font-size:30pt; margin:2px 0 18px; }
.why { list-style:none; counter-reset:why; margin:4px 0 18px; }
.why li { counter-increment:why; position:relative; padding-left:46px; margin-bottom:13px; font-size:13.5pt; line-height:1.5; }
.why li::before { content:counter(why); position:absolute; left:0; top:-1px; width:30px; height:30px; background:#FFF7B0; color:#3f5675; font-family:'Neucha'; font-size:17pt; border-radius:50%; display:flex; align-items:center; justify-content:center; }

/* карточки ценностей */
.cards { display:flex; flex-direction:column; gap:14px; margin-top:10px; }
.card { background:#F4F8FF; border-radius:18px; padding:18px 24px; break-inside:avoid; }
.card-head { display:flex; align-items:center; gap:14px; margin-bottom:7px; }
.card .n { flex:none; width:40px; height:40px; background:#FFF7B0; color:#3f5675; font-family:'Neucha'; font-size:21pt; border-radius:50%; display:flex; align-items:center; justify-content:center; }
.card .t { font-family:'Neucha'; font-size:21pt; color:#7393CC; line-height:1.1; }
.card .d { font-size:12.5pt; line-height:1.55; color:#546A88; }

/* блоки опыта */
.exp { background:#fff; border:2px solid #EAF1FB; border-radius:14px; padding:11px 18px; margin-bottom:9px; break-inside:avoid; }
.exp .h { font-family:'Neucha'; font-size:17.5pt; color:#7393CC; }
.exp .d { font-size:11pt; line-height:1.44; margin-top:2px; }

/* тон голоса */
.say { border-radius:14px; padding:14px 18px; margin:10px 0; font-size:12.5pt; }
.say.yes { background:#EAF7EE; border-left:6px solid #8DCBA0; }
.say.no { background:#FBEFE9; border-left:6px solid #E6A07F; }
.say .lab { font-weight:800; font-size:9pt; text-transform:uppercase; letter-spacing:.12em; display:block; margin-bottom:3px; }
.say.yes .lab { color:#4f9469; }
.say.no .lab { color:#c0764f; }

/* образы характера (§4) */
.connector2 { font-weight:800; color:#3f5675; font-size:13.5pt; margin:14px 0 2px; }
.personas { display:flex; flex-direction:column; gap:10px; margin-top:10px; }
.persona { background:#F4F8FF; border-radius:14px; padding:12px 20px; font-size:12.5pt; line-height:1.5; }
.persona .nm { font-family:'Neucha'; font-size:18pt; color:#7393CC; }

/* простой список с точками (вступление) */
.blist { list-style:none; margin:4px 0 6px; }
.blist li { position:relative; padding-left:26px; margin-bottom:10px; font-size:13.5pt; line-height:1.5; }
.blist li::before { content:''; position:absolute; left:3px; top:9px; width:9px; height:9px; background:#FFF7B0; border-radius:50%; }

/* палитра / стиль */
.swatches { display:flex; gap:12px; margin:14px 0 6px; flex-wrap:wrap; }
.sw { text-align:center; font-size:8.5pt; font-weight:700; }
.sw .chip { width:30mm; height:22mm; border-radius:12px; margin-bottom:5px; border:1px solid rgba(0,0,0,.05); }
.style-row { display:flex; gap:22px; margin-top:14px; }
.style-box { flex:1; background:#F4F8FF; border-radius:16px; padding:16px 18px; }
.style-box .h { font-family:'Neucha'; font-size:17pt; color:#7393CC; margin-bottom:4px; }
.font-neucha { font-family:'Neucha'; font-size:24pt; color:#546A88; }
.font-nunito { font-family:'Nunito'; font-weight:800; font-size:19pt; color:#546A88; }

.slogan-card { background:#7393CC; color:#fff; border-radius:16px; padding:16px 20px; margin:10px 0; }
.slogan-card .role { font-weight:800; font-size:9pt; text-transform:uppercase; letter-spacing:.14em; color:#FFF7B0; }
.slogan-card .txt { font-family:'Neucha'; font-size:22pt; margin-top:3px; }

/* декор */
.deco { position:absolute; opacity:.9; z-index:0; pointer-events:none; }
.deco svg { width:100%; height:100%; display:block; }
.sec-body { position:relative; z-index:1; }

/* финал */
.end { background:#7393CC; color:#fff; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; }
.end .big { font-family:'Neucha'; font-size:40pt; }
.end .sl { font-family:'Neucha'; font-size:20pt; color:#FFF7B0; margin-top:8px; }
.end .credit { margin-top:40px; font-size:9.5pt; opacity:.8; }
"""
# мелкая опечатка-страховка: чиним возможный артефакт
CSS = CSS.replace("#5d7characters", "#5d7390")


def deco(svg, css):
    return '<div class="deco" style="%s">%s</div>' % (css, svg)


PAGES = []

# 1. ОБЛОЖКА
PAGES.append("""
<div class="page cover">
  <div class="logobox"><img src="data:image/png;base64,%s" alt="Мама рядом"></div>
  <div class="kicker">Бренд-платформа</div>
  <div class="title">Мама рядом</div>
  <div class="sub">любовь. поддержка. развитие.</div>
  <div class="for">Кто мы, во что верим и как ведём себя с гостями.<br>Документ для команды, партнёров и подрядчиков.</div>
</div>
""" % LOGO)

# 1b. ВСТУПЛЕНИЕ — что это за документ
PAGES.append("""
<div class="page">
  %s
  <div class="sec-body">
    <h2 class="sec">Что это за документ</h2>
    <p>Это <b>бренд-платформа</b> «Мама рядом» — короткий рассказ о том, кто мы как бренд: во что верим,
    чем отличаемся, как разговариваем с людьми и что они у нас чувствуют.</p>
    <p>Бренд — это <b>не логотип и не вывеска</b>. Это то впечатление, которое остаётся у человека после
    встречи с нами. А бренд-платформа — наша внутренняя договорённость, какими быть, чтобы это
    впечатление складывалось <b>одинаковым везде</b>: в переписке, на ресепшене, в зале, в соцсетях.</p>
    <p class="connector2">Зачем он нужен:</p>
    <ul class="blist">
      <li>чтобы все — администратор, тренер, маркетолог, подрядчик — действовали в одном духе;</li>
      <li>чтобы в спорной ситуации было с чем свериться: «а как бы поступил наш бренд?»;</li>
      <li>чтобы новый человек быстро понял, что у нас за место и как себя вести.</li>
    </ul>
    <p>Это не свод жёстких правил, а <b>ориентир</b>. Читайте, сверяйтесь, возвращайтесь.</p>
  </div>
</div>
""" % deco(CLOUD, "top:14mm;right:-20mm;width:80mm;height:62mm;opacity:.4;"))

# 2. §1a ГЛАВНОЕ — что такое позиционирование + наша мысль
PAGES.append("""
<div class="page">
  %s
  <div class="sec-body">
    <div class="sec-num">01</div>
    <h2 class="sec">Главное о нас</h2>

    <div class="define">
      <span class="lab">Что такое позиционирование</span>
      Это одна-единственная мысль, которую бренд занимает в голове у человека. Не список
      «мы хорошие, чистые, заботливые», а то самое, чем ты отличаешься и по чему тебя запомнят.
      Правило простое: нельзя быть «всем для всех» — надо выбрать одну мысль и владеть ею.
      Спросят про тебя — и в голове всплывает именно она.
    </div>

    <p class="connector">У «Мамы рядом» эта мысль такая:</p>
    <div class="statement">Единственный детский центр, где о маме заботятся не&nbsp;меньше, чем о&nbsp;ребёнке.</div>
  </div>
</div>
""" % deco(HEART, "top:12mm;right:-18mm;width:58mm;height:54mm;opacity:.45;transform:rotate(12deg);"))

# 3. §1b ГЛАВНОЕ — почему именно эта мысль
PAGES.append("""
<div class="page">
  %s
  <div class="sec-body">
    <div class="sec-num">01</div>
    <h3 class="subsec">Почему мы выбрали именно эту мысль</h3>
    <ol class="why">
      <li><b>Свободное место</b> — у конкурентов мама заброшена, никто это поле не занял.</li>
      <li><b>Это правда про нас</b> — мы реально так делаем, не на словах.</li>
      <li><b>Трудно скопировать</b> — это десятки мелочей, а не одна фишка.</li>
      <li><b>Ложится на возраст</b> — в 1,5–4 года опыт и так во многом про маму.</li>
    </ol>
    <p>Когда ребёнку полтора–четыре года, малыш этих лет потом и не вспомнит, а мама проживает
    их рядом, каждое занятие. В обычных центрах она будто лишняя: раздеть в тесном тамбуре, отдать
    тренеру и ждать где-то в сторонке. Мы выбрали обратное — место, где хорошо обоим. Занятие при
    этом настоящее: ребёнок правда растёт, а между ним и мамой крепнет связь. Честно с обеих сторон —
    <b>детям развитие, маме забота, которой нет больше нигде.</b></p>
  </div>
</div>
""" % deco(CLOUD, "bottom:14mm;left:-20mm;width:78mm;height:60mm;opacity:.4;"))

# 3. §2 ОТЛИЧИЕ
PAGES.append("""
<div class="page">
  %s
  <div class="sec-body">
    <div class="sec-num">02</div>
    <h2 class="sec">Чем мы отличаемся</h2>
    <p>Если честно посмотреть на детские центры в городе, к ним относятся как к спортивной секции:
    лишь бы провести занятие. А всё вокруг — чистота, как встретили, удобно ли маме — будто неважно.
    Грязь у входа, обшарпанная раздевалка, администратор, которому всё равно. И ведь работает, люди
    ходят: все привыкли, что так и должно быть.</p>
    <p>Мы так не хотим. Для нас забота и сервис — не милый довесок к занятию, а часть продукта, ровно
    такая же важная, как само занятие. Тот уровень, к которому мама привыкла в хорошем салоне или
    частном садике, мы приносим сюда, в детский центр. И тихо метим поднять планку всему городу:
    чтобы, побывав у нас, к прежнему уже не хотелось возвращаться.</p>
    <p>При этом мы не подменяем одно другим. Занятие — настоящее: ребёнок правда получает пользу,
    мама — настоящую заботу. Не «ходите ради атмосферы», а и то и другое всерьёз.</p>
    <div class="statement" style="font-size:21pt;">Ценой мы не воюем — это самый слабый ход. Стоим чуть
    дороже обычного. И это честно: тепло, чистота и подарки стоят денег. Просто мы считаем, что вы и
    ваш малыш этого достойны.</div>
  </div>
</div>
""" % deco(HEART, "bottom:16mm;right:-16mm;width:54mm;height:50mm;opacity:.4;transform:rotate(-8deg);"))

# 4. §3 ЦЕННОСТИ
VALUES = [
    ("1", "Мама — гость, а не сопровождающий", "Для нас мама — такой же клиент, как и ребёнок, а не просто «та, кто привела». Поэтому ей есть где удобно сесть, поработать, выпить чай и спокойно посмотреть на занятие. Всё, к чему она прикасается, — приятное."),
    ("2", "Сервис — это продукт, а не любезность", "Хороший сервис для нас — это отдельная работа, а не «улыбнёмся, если попросят». Везде чисто по-настоящему: пол, раздевалка, игрушки, туалет. Встречаем по имени, говорим по-доброму. После каждого занятия тренер сам подходит к маме и рассказывает, как прошло у малыша. Многое из этого можно было бы не делать — но мы делаем."),
    ("3", "Ребёнку — настоящий результат", "Ребёнок у нас на самом деле развивается — и мы это маме доносим сами, а не просто заявляем про «уникальную систему занятий», которая по факту часто списана откуда-то. Понятные ступеньки, видно прогресс, а не «отходил — и ладно». И наша задача — самим показывать и рассказывать этот результат маме, не дожидаясь вопросов. Обычно никто толком не рассказывает — а родителю это интересно всегда, даже когда он молчит."),
    ("4", "Среда продумана под ребёнка", "Стойка, лесенка, санузел — на его росте. Игровая, в которой не стыдно. Сменка с антисептиком, чисто и безопасно."),
    ("5", "Честно и прозрачно", "Цены сразу на стойке, без «сейчас посчитаем», и не обещаем того, чего нет. И мы сами высматриваем места, где маме неловко или где она чувствует себя уязвимой как клиент, — и убираем их."),
    ("6", "Забота в мелочах", "Мелочи, которые никто не обязан делать, — это и есть наша забота. Ребёнку — петушок или мыльные пузыри на выходе, маме — патчи или маленький подарок. Забыли вещь — постираем и вернём в подписанном пакете. Из таких мелочей и складывается ощущение, что о тебе правда позаботились."),
]


def render_cards(items):
    return "".join(
        '<div class="card"><div class="card-head"><span class="n">%s</span>'
        '<span class="t">%s</span></div><div class="d">%s</div></div>' % v
        for v in items
    )


PAGES.append("""
<div class="page">
  <div class="sec-body">
    <div class="sec-num">03</div>
    <h2 class="sec">Наши правила</h2>
    <p class="lead">Не лозунги, а правила, по которым мы принимаем решения. Сомневаешься — сверься с ними.</p>
    <div class="cards">%s</div>
  </div>
</div>
""" % render_cards(VALUES[:3]))

PAGES.append("""
<div class="page">
  %s
  <div class="sec-body">
    <div class="sec-num">03</div>
    <h3 class="subsec">Ещё три правила</h3>
    <div class="cards">%s</div>
  </div>
</div>
""" % (deco(FLOWER, "top:14mm;right:-16mm;width:52mm;height:56mm;opacity:.38;"), render_cards(VALUES[3:])))

# 5. §4a ХАРАКТЕР + ОБРАЗЫ
PAGES.append("""
<div class="page">
  %s
  <div class="sec-body">
    <div class="sec-num">04</div>
    <h2 class="sec">Какие мы: характер и тон</h2>
    <p>Если представить бренд человеком — это <b>тёплая, уверенная, современная мама, а заодно
    профессиональный наставник</b>. Рядом с ней спокойно: чувствуешь, что тебя ждали и за тебя уже
    подумали. При этом — без сюсюканья и без давления. Ребёнок для неё — личность, а не «объект
    воспитания», а мама — на равных, как человек, который себя ценит.</p>
    <p class="connector2">Этот характер легко поймать через знакомые образы — по одной черте от каждого:</p>
    <div class="personas">
      <div class="persona"><span class="nm">Миссис Уизли</span> — сердце характера: тёплая материнская любовь. «Тебя здесь ждали», «всё готово, не переживай». Уют без сюсюканья.</div>
      <div class="persona"><span class="nm">Мэри Поппинс</span> — профессионализм с «магией»: развитие через игру, всё продумано за тебя, спокойный контроль без давления.</div>
      <div class="persona"><span class="nm">Мама из «Три кота»</span> — современное, осознанное родительство: спокойно, с уважением к ребёнку, без «надо» и «должен».</div>
      <div class="persona"><span class="nm">Мастер Шифу</span> — система и вера в ребёнка: всё по шагам, мы знаем, как правильно развивать, а не «просто поиграли».</div>
      <div class="persona"><span class="nm">Радость</span> <span style="opacity:.55">(Головоломка)</span> — про эмоции: ребёнок не просто занимается, а радуется. Впечатления, а не только польза.</div>
    </div>
  </div>
</div>
""" % deco(HEART, "top:12mm;right:-16mm;width:50mm;height:46mm;opacity:.4;transform:rotate(10deg);"))

# 6. §4b КАК МЫ ГОВОРИМ
PAGES.append("""
<div class="page">
  %s
  <div class="sec-body">
    <div class="sec-num">04</div>
    <h3 class="subsec">Как мы говорим</h3>
    <p>Как заботливая, уверенная подруга — но на «вы». Тепло, по-человечески, без канцелярита:
    никаких «ваша заявка принята в обработку». По имени и по-доброму. Коротко и по делу — у мамы
    мало времени, лишнего не льём. И спокойно, без впаривания: помогаем выбрать, а не «продаём».
    К маме — на «вы», к малышу — на «ты» (ему два года, «вы» звучит странно).</p>
    <div class="say yes"><span class="lab">так — да</span>«Аня, добрый день! Соню записала на субботу, 10:00. Поменяются планы — напишите, подвинем 🙂»</div>
    <div class="say yes"><span class="lab">так — да</span>«С малышом не всегда угадаешь по времени — подберём слот, который реально удобен.»</div>
    <div class="say no"><span class="lab">так — нет</span>«Здравствуйте. Ваша заявка принята в обработку. Ожидайте звонка оператора.»</div>
  </div>
</div>
""" % deco(FLOWER, "bottom:14mm;left:-18mm;width:56mm;height:60mm;opacity:.4;"))

# 6. §5 ОПЫТ КЛИЕНТА
EXP = [
    ("Встреча и вход", "Мама с малышом заходят — и их встречают: улыбкой, по имени. Помогают переобуться, с заботой о здоровье: антисептик, нормальная сменка, а не одноразовый носок на босу ногу. Коляску и самокат есть куда поставить, под крышей. Первое, что чувствуешь: тут чисто и тебе рады."),
    ("Пока идёт занятие — время мамы", "Малыш на занятии, а мама не толпится в тамбуре. Есть где сесть: мягкий диван или место с розеткой, если надо поработать. Горячая ромашка, нормальный кофе, вода, лёгкий перекус. За занятием можно спокойно наблюдать. Этот час — не «ожидание», а маленькая пауза для себя."),
    ("Мир, сделанный под ребёнка", "Всё вокруг — на его рост: стойка, лесенка, раковина, до которых он дотягивается сам. Игровая, в которой ему интересно, а маме не стыдно. Малыш сразу понимает: это место для него."),
    ("Ребёнку хочется возвращаться", "За старание — наклейка, за наклейки — приз; монетки, которые тратят в маленьком магазинчике; дневничок, где видно, как он растёт. Маленькие радости, ради которых ждёшь следующего занятия."),
    ("И мелочи на выходе", "Малышу — петушок или мыльные пузыри, маме — иногда патч или маленький сюрприз. Забыли вещь — постираем и вернём, а не сунем в коробку. Из такого и остаётся тёплое «сюда хочется вернуться»."),
]
exps = "".join('<div class="exp"><div class="h">%s</div><div class="d">%s</div></div>' % e for e in EXP)
PAGES.append("""
<div class="page">
  <div class="sec-body">
    <div class="sec-num">05</div>
    <h2 class="sec">Как у нас всё устроено</h2>
    <p class="lead">От порога до выхода — что мама и малыш реально видят и чувствуют.</p>
    %s
  </div>
</div>
""" % exps)

# 7. §6 ИМЯ · СЛОГАНЫ · СТИЛЬ
SW = [("#7393CC","синий"),("#FFF7B0","жёлтый"),("#FFE5D1","персик"),("#546A88","тёмно-синий"),("#CFE1FF","голубой")]
swatches = "".join('<div class="sw"><div class="chip" style="background:%s"></div>%s<br>%s</div>' % (c, c, n) for c, n in SW)
PAGES.append("""
<div class="page">
  <div class="sec-body">
    <div class="sec-num">06</div>
    <h2 class="sec">Имя, слоганы и стиль</h2>
    <p>Имя — про близость с двух сторон. <b>Мама рядом</b> — с ребёнком: ему спокойно, есть на кого
    опереться, чтобы расти и пробовать новое. А мы — <b>рядом с мамой</b>: о ней самой есть кому
    позаботиться. Так и держим: <b>мама рядом — а мы рядом с мамой.</b></p>

    <h3 style="font-size:20pt;margin:14px 0 4px;">Две строки — у каждой своя работа</h3>
    <div class="slogan-card"><span class="role">подпись под логотипом</span><div class="txt">любовь. поддержка. развитие.</div></div>
    <div class="slogan-card"><span class="role">в рекламе и общении</span><div class="txt">Детям — развитие, маме — заботу</div></div>

    <h3 style="font-size:20pt;margin:18px 0 2px;">Цвета</h3>
    <div class="swatches">%s</div>

    <div class="style-row">
      <div class="style-box"><div class="h">Шрифты</div>
        <div class="font-neucha">Neucha — акцент</div>
        <div class="font-nunito" style="margin-top:6px;">Nunito Sans — текст</div>
      </div>
      <div class="style-box"><div class="h">Логотип и элементы</div>
        <div style="font-size:10.5pt;line-height:1.5;">Рука мамы, в ней детская ладошка — «мама рядом», забота, вместе.
        Тёплые рисованные элементы: сердце, ромашка, облачко.</div>
        <div style="display:flex;gap:8px;margin-top:8px;">
          <div style="width:16mm;height:16mm;">%s</div>
          <div style="width:16mm;height:16mm;">%s</div>
          <div style="width:16mm;height:16mm;">%s</div>
        </div>
      </div>
    </div>
  </div>
</div>
""" % (swatches, HEART, FLOWER, CLOUD))

# 8. ФИНАЛ
PAGES.append("""
<div class="page end">
  <div class="big">Мама рядом</div>
  <div class="sl">Детям — развитие, маме — заботу</div>
  <div class="credit">Бренд-платформа · визуальный стиль: @diana_alexseevna</div>
</div>
""")

HTML = (
    "<!doctype html><html lang='ru'><head><meta charset='utf-8'>"
    "<style>%s\n%s</style></head><body>%s</body></html>"
    % (FONTS, CSS, "".join(PAGES))
)

OUT_HTML.write_text(HTML, encoding="utf-8")
print("HTML собран:", OUT_HTML, "(%.1f КБ)" % (len(HTML.encode()) / 1024))
