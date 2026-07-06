# -*- coding: utf-8 -*-
"""Быстрая симуляция 'от обратного': какие улучшения делают модель плюсовой.
Движок = тот же, что в build_model_v4.py (уровень = decay + новые покупатели).
Горизонт авг-2026 .. дек-2028 (29 мес).
"""

SEAS = {  # месяц: (коэф притока заявок, коэф конверсии в покупку)
    1: (1.0, 0.6), 2: (1.4, 1.0), 3: (1.1, 1.0), 4: (1.0, 1.0),
    5: (1.0, 1.0), 6: (0.6, 0.9), 7: (0.5, 0.9), 8: (0.7, 1.0),
    9: (1.2, 1.0), 10: (1.1, 1.0), 11: (1.0, 1.0), 12: (0.8, 0.8),
}
PAY_RATE = 0.93         # зачислен -> оплатил
CONV_PAID = 0.13
CONV_ORG = 0.23
TRIAL_SHARE = 0.5       # доля заявок, дошедших до пробного
TRIAL_PRICE = 900
CAP = 250

FIX_OTHER = 435_000     # аренда и т.п.
FOT_CORE = 350_000
GROUP_RATE, KID_RATE = 500, 100
MIN_GROUPS = 30
FILL = 4.0

CASH0 = 3_000_000 - 1_551_733   # 1 448 267
CAPEX_AUG = 1_700_000
TAXES_FIXED = {(2026, 8): 38_260, (2026, 12): 40_000}  # как в исходнике

MONTHS = []
y, m = 2026, 8
for _ in range(29):
    MONTHS.append((y, m))
    m += 1
    if m == 13:
        m, y = 1, y + 1


def run(name, avg_pay, dur, buys, org0, org_growth, org_cap,
        ch2_start_idx, ch2_leads, ch2_budget, ref_rate,
        target_leads=130, cpl=800, usn=False,
        fot_core=FOT_CORE, price_bump_idx=None, price_bump=0.0):
    life = buys * dur
    nomin0 = avg_pay / dur
    level, cash = 0.0, CASH0
    dno, dno_m = cash, None
    first_plus = None
    rows = []
    for i, (yy, mm) in enumerate(MONTHS):
        nomin = nomin0 * (1 + price_bump) if (price_bump_idx is not None and i >= price_bump_idx) else nomin0
        si, sc = SEAS[mm]
        leads_paid = target_leads * si
        leads_org = min(org_cap, org0 * (1 + org_growth) ** i) * si
        leads_ch2 = (ch2_leads * si) if i >= ch2_start_idx else 0.0
        buyers_ads = (leads_paid * CONV_PAID + leads_org * CONV_ORG
                      + leads_ch2 * CONV_PAID) * sc * PAY_RATE
        buyers_ref = ref_rate * level * sc          # рефералка от размера базы
        buyers = buyers_ads + buyers_ref
        level = min(CAP, level * (1 - 1 / life) + buyers)

        trials = (leads_paid + leads_org + leads_ch2) * TRIAL_SHARE * sc
        rev = level * nomin + max(0.0, trials - buyers) * TRIAL_PRICE
        teachers = max(MIN_GROUPS, level / FILL) * 4.33 * GROUP_RATE + level * 4.33 * KID_RATE
        costs = FIX_OTHER + fot_core + teachers + target_leads * cpl \
            + (ch2_budget if i >= ch2_start_idx else 0) \
            + TAXES_FIXED.get((yy, mm), 0)
        if usn:
            costs += rev * 0.06
        op = rev - costs
        cash += op - (CAPEX_AUG if i == 0 else 0)
        if op > 0 and first_plus is None:
            first_plus = f"{mm:02d}.{yy}"
        if cash < dno:
            dno, dno_m = cash, f"{mm:02d}.{yy}"
        rows.append((yy, mm, level, buyers, rev, op, cash))

    lvl_d27 = next(r[2] for r in rows if r[:2] == (2027, 12))
    op_d28 = rows[-1][5]
    y28 = sum(r[5] for r in rows if r[0] == 2028)
    print(f"\n=== {name} (УСН {'да' if usn else 'нет'}) ===")
    print(f"  жизнь {life:.1f} мес · с клиента {nomin0:,.0f} ₽/мес · LTV {avg_pay*buys:,.0f}")
    print(f"  клиентов: дек-27 {lvl_d27:.0f} · дек-28 {rows[-1][2]:.0f}")
    print(f"  первый плюс: {first_plus or 'НИКОГДА'} · опер/мес в конце: {op_d28:,.0f}")
    print(f"  2028 операционно: {y28:,.0f}/год")
    print(f"  дно кассы: {dno:,.0f} ({dno_m}) → всего денег нужно ≈ {3_000_000 + max(0, -dno):,.0f}")
    print(f"  касса дек-28: {cash:,.0f}")
    return rows


# S0 — вводные юзера как есть: месячные преобладают, органика ~5 покупателей, без рефералки
for usn in (False, True):
    run("S0 Как сейчас (месячные, органика 5, без рефералки)",
        avg_pay=6_240, dur=1.2, buys=3.0,
        org0=23, org_growth=0.0, org_cap=25,
        ch2_start_idx=999, ch2_leads=0, ch2_budget=0,
        ref_rate=0.0, usn=usn)

# S1 — реалистично-улучшенный: 2-мес дефолт (45%), жизнь 4.0, карты/район растут,
#      второй канал с октября, рефералка 4% базы/мес
for usn in (False, True):
    run("S1 Реалистично-улучшенный",
        avg_pay=9_040, dur=1.54, buys=2.6,
        org0=15, org_growth=0.05, org_cap=50,
        ch2_start_idx=2, ch2_leads=30, ch2_budget=30_000,
        ref_rate=0.04, usn=usn)

# S2 — цель: продления 3.0, рефералка 6%, органика до 60, 2-мес 55%
for usn in (False, True):
    run("S2 Цель (всё получилось)",
        avg_pay=9_380, dur=1.59, buys=3.0,
        org0=15, org_growth=0.06, org_cap=60,
        ch2_start_idx=2, ch2_leads=40, ch2_budget=40_000,
        ref_rate=0.06, usn=usn)

# S3 — «интересный»: S2 + деньги с клиента (2-мес 60% + единый/индив 15% → платёж 10 450,
#      прайс +8% с сен-2027) + ФОТ-ядро 300к
for usn in (False, True):
    run("S3 Интересный (S2 + деньги с клиента + ФОТ 300)",
        avg_pay=10_450, dur=1.735, buys=3.0,
        org0=15, org_growth=0.06, org_cap=60,
        ch2_start_idx=2, ch2_leads=40, ch2_budget=40_000,
        ref_rate=0.06, usn=usn,
        fot_core=300_000, price_bump_idx=13, price_bump=0.08)

# S3-чувствительность: тот же S3, но рефералка 4% (если программа слабее)
run("S3, но рефералка лишь 4%",
    avg_pay=10_450, dur=1.735, buys=3.0,
    org0=15, org_growth=0.06, org_cap=60,
    ch2_start_idx=2, ch2_leads=40, ch2_budget=40_000,
    ref_rate=0.04, usn=True,
    fot_core=300_000, price_bump_idx=13, price_bump=0.08)
