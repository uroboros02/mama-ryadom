# -*- coding: utf-8 -*-
"""Свип по жизни клиента: 3/4/5/6/7 мес при прочих равных «докрученной».
Тарифы (платёж 11 068, длительность 1,8 → 6 149 ₽/мес), рефералка 6%, карты 15→60,
2-й канал 40 заявок, прайс +8% сен-27 +6% сен-28, ФОТ 300к. Горизонт до дек-2029, УСН вкл.
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
CH2_IDX, CH2_LEADS, CH2_BUDGET = 2, 40, 40_000
REF, FOT = 0.06, 300_000
BUMPS = ((13, 1.08), (25, 1.08 * 1.06))
TARGET, CPL = 130, 800


def run(life):
    buys = life / DUR
    nomin0 = AVG_PAY / DUR
    level, cash = 0.0, CASH0
    first_plus = first500 = None
    dno = cash
    lv = {}
    y2029 = 0.0
    for i, (yy, mm) in enumerate(MONTHS):
        pf = 1.0
        for idx, f in BUMPS:
            if i >= idx:
                pf = f
        nomin = nomin0 * pf
        si, sc = SEAS[mm]
        lp = TARGET * si
        lo = min(ORG_CAP, ORG0 * (1 + ORG_G) ** i) * si
        lc = (CH2_LEADS * si) if i >= CH2_IDX else 0.0
        buyers = ((lp + lc) * CONV_PAID + lo * CONV_ORG) * sc * PAY_RATE + REF * level * sc
        level = min(CAP, level * (1 - 1 / life) + buyers)
        trials = (lp + lo + lc) * TRIAL_SHARE * sc
        rev = level * nomin + max(0.0, trials - buyers) * TRIAL_PRICE
        teachers = max(MIN_GROUPS, level / FILL) * 4.33 * GROUP_RATE + level * 4.33 * KID_RATE
        costs = FIX_OTHER + FOT + teachers + TARGET * CPL \
            + (CH2_BUDGET if i >= CH2_IDX else 0) + TAXES_FIXED.get((yy, mm), 0) + rev * 0.06
        op = rev - costs
        cash += op - (CAPEX_AUG if i == 0 else 0)
        if op > 0 and first_plus is None:
            first_plus = f"{RU[mm]}-{yy % 100:02d}"
        if op >= 500_000 and first500 is None:
            first500 = f"{RU[mm]}-{yy % 100:02d}"
        dno = min(dno, cash)
        if mm == 12:
            lv[yy] = level
        if yy == 2029:
            y2029 += op
    ltv = AVG_PAY * buys
    total_need = 3_000_000 + max(0, -dno)
    print(f"жизнь {life} мес | покупок {buys:.1f} | LTV {ltv/1000:5.1f}к | "
          f"кл дек-27 {lv[2027]:3.0f} дек-28 {lv[2028]:3.0f} дек-29 {lv[2029]:3.0f} | "
          f"плюс: {first_plus or '—':>7} | 500к: {first500 or '—':>7} | "
          f"всего {total_need/1e6:4.1f} млн | 2029: {y2029/1e6:+5.2f} млн/год | касса дек-29 {cash/1e6:+5.1f} млн")


print("Свип по жизни клиента (всё остальное = «докрученная»):")
for life in (3, 4, 5, 6, 7):
    run(life)
