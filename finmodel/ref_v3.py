import importlib.util, io, contextlib, math
spec = importlib.util.spec_from_file_location('sim_v3', '/Users/nikolaymacbook/Claude/mama-ryadom-bot/finmodel/sim_v3.py')
m = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(m)

def run(s, usn=True):
    preN = s['se75'] + s['se50'] + s['se40'] + s['se30']
    preCash = (s['se75']*0.25 + s['se50']*0.50 + s['se40']*0.60 + s['se30']*0.70)*s['nomin']*s['preLen']
    if usn: preCash *= 0.94
    A, cash = float(s['startBase']) + preN, s['plan'] - m.SPENT + preCash
    preA = float(preN)
    y29 = 0.0
    for i in range(m.N):
        mm = m.MONTHS[i][1]; si, sc = m.SEAS[mm]
        pf = ((1 + s['bump1']/100) if i >= 13 else 1) * ((1 + s['bump2']/100) if i >= 25 else 1)
        boost = i < s['boostM']
        B = s['buyersBoost'] if boost else s['buyers']
        cplx = s['boostCpl'] if boost else s['cpl']
        leads = B / ((s['l2t']/100) * (s['t2p']/100) * m.PAY)
        lp = leads * si
        lo = min(s['orgCap'], s['org0'] * (1 + s['orgg']/100) ** i) * si
        nw = B*si*sc + lo*(s['co']/100)*sc*m.PAY + (s['ref']/100)*A*sc
        A = min(s['cap'], A*(1 - 1/s['life']) + nw)
        preB = preA
        preA *= (1 - 1/s['life'])
        if i == math.ceil(s['preLen']) and preB > 0:
            extra = preB*(s['preChurn']/100 - 1/s['life'])
            preA -= extra; A = min(s['cap'], max(0.0, A - extra))
        tr = (lp*(s['l2t']/100) + lo*(s['trial']/100)) * sc
        cov = min(1.0, max(0.0, s['preLen'] - i))
        rev = A*s['nomin']*pf + max(0, tr - nw)*900 - preA*s['nomin']*pf*cov
        groups = max(s['gmin'], A*s['vis']/(4.33*s['fill']))
        teach = groups*4.33*s['rateG'] + A*s['vis']*s['rateC']
        tax = (38260 if i == 0 else 0) + (40000 if i == 4 else 0) + (0.06*rev if usn else 0)
        pnl = rev - leads*cplx - s['other'] - s['fot'] - teach - tax
        cash += pnl - (s['rebuild'] if i == 0 else 0)
        if m.MONTHS[i][0] == 2029: y29 += pnl
    def be():
        bud = s['buyers']/((s['l2t']/100)*(s['t2p']/100)*m.PAY)*s['cpl']
        for X in range(0, int(s['cap'])+1):
            rev = X*s['nomin']
            g = max(s['gmin'], X*s['vis']/(4.33*s['fill']))
            if rev >= bud + s['other'] + s['fot'] + g*4.33*s['rateG'] + X*s['vis']*s['rateC'] + 0.06*rev:
                return X
    return cash, A, y29, be()

for name, s in [('Как сейчас', m.BASE), ('Зал 60% · жизнь 3', m.HALL), ('Докрученная', m.DOKR),
                ('+ Форсаж', m.FORS), ('Мечта: жизнь 6', m.DREAM)]:
    cash, A, y29, be = run(s)
    print(f"{name} | {cash:.4f} | {A:.6f} | {y29:.4f} | {be}")
