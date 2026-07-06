# -*- coding: utf-8 -*-
"""Две таблицы: отсчётная (вводные как есть) и докрученная (до первых ~500к/мес).
Горизонт авг-2026 .. дек-2029 (41 мес). Всё с УСН 6%. Движок = build_model_v4.
"""

SEAS = {
    1: (1.0, 0.6), 2: (1.4, 1.0), 3: (1.1, 1.0), 4: (1.0, 1.0),
    5: (1.0, 1.0), 6: (0.6, 0.9), 7: (0.5, 0.9), 8: (0.7, 1.0),
    9: (1.2, 1.0), 10: (1.1, 1.0), 11: (1.0, 1.0), 12: (0.8, 0.8),
}
PAY_RATE, CONV_PAID, CONV_ORG = 0.93, 0.13, 0.23
TRIAL_SHARE, TRIAL_PRICE, CAP = 0.5, 900, 250
FIX_OTHER = 435_000
GROUP_RATE, KID_RATE, MIN_GROUPS, FILL = 500, 100, 30, 4.0
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


def run(name, avg_pay, dur, buys, org0, org_growth, org_cap,
        ch2_start_idx, ch2_leads, ch2_budget, ref_rate,
        fot_core, price_bumps=(), target_leads=130, cpl=800):
    life = buys * dur
    nomin0 = avg_pay / dur
    level, cash = 0.0, CASH0
    first500 = None
    rows = []
    for i, (yy, mm) in enumerate(MONTHS):
        pf = 1.0
        for idx, f in price_bumps:
            if i >= idx:
                pf = f
        nomin = nomin0 * pf
        si, sc = SEAS[mm]
        leads_paid = target_leads * si
        leads_org = min(org_cap, org0 * (1 + org_growth) ** i) * si
        leads_ch2 = (ch2_leads * si) if i >= ch2_start_idx else 0.0
        buyers = ((leads_paid + leads_ch2) * CONV_PAID + leads_org * CONV_ORG) * sc * PAY_RATE \
            + ref_rate * level * sc
        level = min(CAP, level * (1 - 1 / life) + buyers)
        trials = (leads_paid + leads_org + leads_ch2) * TRIAL_SHARE * sc
        rev = level * nomin + max(0.0, trials - buyers) * TRIAL_PRICE
        teachers = max(MIN_GROUPS, level / FILL) * 4.33 * GROUP_RATE + level * 4.33 * KID_RATE
        costs = FIX_OTHER + fot_core + teachers + target_leads * cpl \
            + (ch2_budget if i >= ch2_start_idx else 0) \
            + TAXES_FIXED.get((yy, mm), 0) + rev * 0.06
        op = rev - costs
        cash += op - (CAPEX_AUG if i == 0 else 0)
        if op >= 500_000 and first500 is None:
            first500 = f"{RU[mm]}-{yy}"
        rows.append((yy, mm, level, rev, costs, op, cash))

    print(f"\n===== {name} =====")
    print(f"жизнь клиента {life:.1f} мес · с клиента {nomin0:,.0f} ₽/мес (до индексаций) · первый месяц ≥500к: {first500 or 'НЕТ за 41 мес'}")
    print(f"{'месяц':>8} | {'клиентов':>8} | {'выручка':>9} | {'расходы':>9} | {'приб/мес':>9} | {'касса':>10}")
    show = {0, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34, 37, 40}
    for i, (yy, mm, lvl, rev, c, op, cash) in enumerate(rows):
        if i in show:
            print(f"{RU[mm]}-{yy%100:02d}".rjust(8) + f" | {lvl:8.0f} | {rev/1000:9,.0f} | {c/1000:9,.0f} | {op/1000:+9,.0f} | {cash/1000:+10,.0f}")
    dno = min(r[6] for r in rows)
    print(f"дно кассы: {dno/1000:+,.0f} тыс → всего денег ≈ {(3_000_000 + max(0,-dno))/1e6:.1f} млн; 2029 операционно: {sum(r[5] for r in rows if r[0]==2029)/1e6:+.2f} млн/год")


# ОТСЧЁТНАЯ: вводные юзера как есть (месячные ~80%, органика ~5 покупателей, без рефералки,
# без 2-го канала, ФОТ 350, прайс фикс)
run("ОТСЧЁТНАЯ (вводные как есть)",
    avg_pay=6_240, dur=1.2, buys=3.0,
    org0=23, org_growth=0.0, org_cap=25,
    ch2_start_idx=999, ch2_leads=0, ch2_budget=0,
    ref_rate=0.0, fot_core=350_000)

# ДОКРУЧЕННАЯ: микс 15% мес / 60% 12-зан / 15% единый / 10% индив (платёж 11 068, дл 1.80),
# покупок 3, рефералка 6%, карты/район 15→60 заявок, 2-й канал 40 заявок с окт-26,
# прайс +8% сен-27 и ещё +6% сен-28, ФОТ-ядро 300к
run("ДОКРУЧЕННАЯ (до первых ~500к/мес)",
    avg_pay=11_068, dur=1.80, buys=3.0,
    org0=15, org_growth=0.06, org_cap=60,
    ch2_start_idx=2, ch2_leads=40, ch2_budget=40_000,
    ref_rate=0.06, fot_core=300_000,
    price_bumps=((13, 1.08), (25, 1.08 * 1.06)))
