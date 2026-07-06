# -*- coding: utf-8 -*-
"""Маркетинг-форсаж на старте: докрученная, но авг-26..дек-27 таргет 220 лидов @ CPL 1200
(+ 2-й канал 80 заявок @ 96к с окт-26), потом откат к 130 @ 800 (+40 @ 40к).
Сравнение с обычной докрученной. Плюс контрольный прогон: форсаж при жизни 4 мес.
"""

SEAS = {
    1: (1.0, 0.6), 2: (1.4, 1.0), 3: (1.1, 1.0), 4: (1.0, 1.0),
    5: (1.0, 1.0), 6: (0.6, 0.9), 7: (0.5, 0.9), 8: (0.7, 1.0),
    9: (1.2, 1.0), 10: (1.1, 1.0), 11: (1.0, 1.0), 12: (0.8, 0.8),
}
PAY_RATE, CONV_PAID, CONV_ORG = 0.93, 0.13, 0.23
TRIAL_SHARE, TRIAL_PRICE, CAP = 0.5, 900, 250
FIX_OTHER, GROUP_RATE, KID_RATE, MIN_GROUPS, FILL = 435_000, 500, 100, 30, 4.0
CASH0 = 3_000_000 - 1_551_733
CAPEX_AUG = 1_700_000
TAXES_FIXED = {(2026, 8): 38_260, (2026, 12): 40_000}

N = 41
MONTHS = []
y, m = 2026, 8
for _ in range(N):
    MONTHS.append((y, m))
    m += 1
    if m == 13:
        m, y = 1, y + 1
RU = {1:'янв',2:'фев',3:'мар',4:'апр',5:'май',6:'июн',7:'июл',8:'авг',9:'сен',10:'окт',11:'ноя',12:'дек'}

AVG_PAY, DUR = 11_068, 1.80
ORG0, ORG_G, ORG_CAP = 15, 0.06, 60
REF, FOT = 0.06, 300_000
BUMPS = ((13, 1.08), (25, 1.08 * 1.06))


def run(name, life, boost=False, boost_end=17, table=False):
    nomin0 = AVG_PAY / DUR
    level, cash = 0.0, CASH0
    first_plus = first500 = None
    dno, dno_m = cash, None
    lv, y29 = {}, 0.0
    rows = []
    for i, (yy, mm) in enumerate(MONTHS):
        pf = 1.0
        for idx, f in BUMPS:
            if i >= idx:
                pf = f
        nomin = nomin0 * pf
        si, sc = SEAS[mm]
        if boost and i <= boost_end:
            tgt, cpl = 220, 1200
            ch2, ch2b = (80, 96_000) if i >= 2 else (0, 0)
        else:
            tgt, cpl = 130, 800
            ch2, ch2b = (40, 40_000) if i >= 2 else (0, 0)
        lp = tgt * si
        lo = min(ORG_CAP, ORG0 * (1 + ORG_G) ** i) * si
        lc = ch2 * si
        buyers = ((lp + lc) * CONV_PAID + lo * CONV_ORG) * sc * PAY_RATE + REF * level * sc
        level = min(CAP, level * (1 - 1 / life) + buyers)
        trials = (lp + lo + lc) * TRIAL_SHARE * sc
        rev = level * nomin + max(0.0, trials - buyers) * TRIAL_PRICE
        teachers = max(MIN_GROUPS, level / FILL) * 4.33 * GROUP_RATE + level * 4.33 * KID_RATE
        costs = FIX_OTHER + FOT + teachers + tgt * cpl + ch2b \
            + TAXES_FIXED.get((yy, mm), 0) + rev * 0.06
        op = rev - costs
        cash += op - (CAPEX_AUG if i == 0 else 0)
        if op > 0 and first_plus is None:
            first_plus = f"{RU[mm]}-{yy % 100:02d}"
        if op >= 500_000 and first500 is None:
            first500 = f"{RU[mm]}-{yy % 100:02d}"
        if cash < dno:
            dno, dno_m = cash, f"{RU[mm]}-{yy % 100:02d}"
        if mm == 12:
            lv[yy] = level
        if yy == 2029:
            y29 += op
        rows.append((yy, mm, level, rev, costs, op, cash))

    print(f"\n=== {name} ===")
    print(f"первый плюс: {first_plus or '—'} · первые 500к: {first500 or '—'} · дно {dno/1e6:+.1f} млн ({dno_m}) "
          f"→ всего ≈ {(3e6 + max(0, -dno))/1e6:.1f} млн · кл дек-27/28/29: {lv[2027]:.0f}/{lv[2028]:.0f}/{lv[2029]:.0f} · "
          f"2029 {y29/1e6:+.2f} млн/год · касса дек-29 {cash/1e6:+.1f} млн")
    if table:
        show = {0, 4, 7, 10, 13, 16, 19, 22, 28, 34, 40}
        print(f"{'месяц':>8} | {'клиентов':>8} | {'выручка':>9} | {'расходы':>9} | {'приб/мес':>9} | {'касса':>10}")
        for i, (yy, mm, lvl, rev, c, op, csh) in enumerate(rows):
            if i in show:
                print(f"{RU[mm]}-{yy%100:02d}".rjust(8) + f" | {lvl:8.0f} | {rev/1000:9,.0f} | {c/1000:9,.0f} | {op/1000:+9,.0f} | {csh/1000:+10,.0f}")


run("Докрученная (референс, жизнь 5,4 мес)", life=5.4, boost=False)
run("Докрученная + МАРКЕТИНГ-ФОРСАЖ до дек-27 (жизнь 5,4)", life=5.4, boost=True, table=True)
run("Форсаж, но удержание НЕ получилось (жизнь 4)", life=4.0, boost=True)
run("Форсаж при жизни 6 (всё получилось)", life=6.0, boost=True)
