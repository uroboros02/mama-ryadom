# -*- coding: utf-8 -*-
"""Движок v3.3: рычаг = платных покупателей/мес (CPL 1000 средний, бюджет производный),
платная воронка = два рычага l2t×t2p (заявка→пробное 30% × пробное→покупка 40%; факт
SportCRM авг24-июл26: запись 38.5%, из записанных купили 28%, сквозная 11%),
пробные платных по l2t, органики — по trial. Тренеры от посещаемости 2/мес, потолок 760."""

import math
SEAS = {1:(1.0,0.6),2:(1.4,1.0),3:(1.1,1.0),4:(1.0,1.0),5:(1.0,1.0),6:(0.6,0.9),
        7:(0.5,0.9),8:(0.7,1.0),9:(1.2,1.0),10:(1.1,1.0),11:(1.0,1.0),12:(0.8,0.8)}
PAY, N, SPENT = 0.93, 41, 1551733
MONTHS=[]; y,m=2026,8
for _ in range(N):
    MONTHS.append((y,m)); m+=1
    if m==13: m,y=1,y+1
RU={1:'янв',2:'фев',3:'мар',4:'апр',5:'май',6:'июн',7:'июл',8:'авг',9:'сен',10:'окт',11:'ноя',12:'дек'}
lbl=lambda i:f"{RU[MONTHS[i][1]]}-{MONTHS[i][0]%100:02d}"

BASE=dict(buyers=16,cpl=1000,l2t=30,t2p=40,trial=50,org0=23,orgg=0,orgCap=25,co=23,
          se75=0,se50=0,se40=0,se30=0,preLen=2,preChurn=50,   # предпродажа июля: шт по скидкам + длит. (мес) + отток на обрыве (%)
          buyersBoost=36,boostCpl=1200,bump1=0,bump2=0,
          other=435000,fot=350000,rateG=500,rateC=100,gmin=30,fill=4,vis=2.0,
          plan=3000000,rebuild=1700000,startBase=0,cap=760,
          life=3.0,nomin=5200,ref=0,boostM=0)
DOKR={**BASE,**dict(life=5.4,nomin=6150,ref=6,buyers=21,org0=15,orgg=6,orgCap=60,bump1=8,bump2=6,fot=300000)}
FORS={**DOKR,**dict(boostM=18)}
DREAM={**FORS,**dict(life=6.0)}
HALL={**BASE,**dict(buyers=165)}   # «Зал 60% · жизнь 3»: средняя база-2029 ≈ 456 (60% от 760)

def run(name,s,usn=True,detail=False):
    preN=s['se75']+s['se50']+s['se40']+s['se30']
    preCash=(s['se75']*0.25+s['se50']*0.50+s['se40']*0.60+s['se30']*0.70)*s['nomin']*s['preLen']
    if usn: preCash*=0.94
    A,cash=float(s['startBase'])+preN,s['plan']-SPENT+preCash
    preA=float(preN)
    fp=f5=None; dno,dno_i=cash,0; y28=y29=0.0; lv={}
    mkt_sum=0
    for i in range(N):
        mm=MONTHS[i][1]; si,sc=SEAS[mm]
        pf=((1+s['bump1']/100) if i>=13 else 1)*((1+s['bump2']/100) if i>=25 else 1)
        boost=i<s['boostM']
        B=s['buyersBoost'] if boost else s['buyers']
        cplx=s['boostCpl'] if boost else s['cpl']
        leads=B/((s['l2t']/100)*(s['t2p']/100)*PAY)   # платных лидов надо купить (воронка заявка→пробное→покупка)
        lp=leads*si
        lo=min(s['orgCap'],s['org0']*(1+s['orgg']/100)**i)*si
        nw=B*si*sc + lo*(s['co']/100)*sc*PAY + (s['ref']/100)*A*sc
        A=min(s['cap'],A*(1-1/s['life'])+nw)
        preB=preA
        preA*=(1-1/s['life'])                            # скидочная когорта тает общим оттоком
        if i==math.ceil(s['preLen']) and preB>0:         # обрыв: скидочный абонемент кончился — отток когорты = preChurn
            extra=preB*(s['preChurn']/100-1/s['life'])
            preA-=extra; A=min(s['cap'],max(0.0,A-extra))
        tr=(lp*(s['l2t']/100)+lo*(s['trial']/100))*sc   # пробные: платные по l2t, органика по trial
        cov=min(1.0,max(0.0,s['preLen']-i))             # какую долю месяца предпродажники уже оплатили
        rev=A*s['nomin']*pf+max(0,tr-nw)*900-preA*s['nomin']*pf*cov
        groups=max(s['gmin'],A*s['vis']/(4.33*s['fill']))
        teach=groups*4.33*s['rateG']+A*s['vis']*s['rateC']
        mkt=leads*cplx
        tax=(38260 if i==0 else 0)+(40000 if i==4 else 0)+(0.06*rev if usn else 0)
        pnl=rev-mkt-s['other']-s['fot']-teach-tax
        cash+=pnl-(s['rebuild'] if i==0 else 0)
        if pnl>0 and fp is None: fp=i
        if pnl>=500000 and f5 is None: f5=i
        if cash<dno: dno,dno_i=cash,i
        if MONTHS[i][0]==2028: y28+=pnl
        if MONTHS[i][0]==2029: y29+=pnl
        if mm==12: lv[MONTHS[i][0]]=A
        mkt_sum=mkt
    short=max(0,-dno)
    cac=s['cpl']/((s['l2t']/100)*(s['t2p']/100)*PAY)
    print(f"{name:16s} плюс {lbl(fp) if fp is not None else '—':7s} 500к {lbl(f5) if f5 is not None else '—':7s} "
          f"дно {dno/1e6:+5.1f} ({lbl(dno_i)}) всего {(s['plan']+short)/1e6:4.1f} "
          f"кл дек 27/28/29 {lv[2027]:3.0f}/{lv[2028]:3.0f}/{lv[2029]:3.0f} "
          f"2029 {y29/1e6:+5.2f}/год касса29 {cash/1e6:+5.1f} | CAC {cac:,.0f}₽ бюджет {mkt_sum/1000:.0f}к/мес")
    return cash

print("=== ТРЕНАЖЁР v3 (визиты 2, потолок 760, рычаг-покупатели, CPL 1000) ===")
run("Как сейчас", BASE)
run("Зал 60% ж3 ", HALL)
run("Докрученная", DOKR)
run("+ Форсаж", FORS)
run("Мечта жизнь 6", DREAM)

print("\n=== было в v2 (для сравнения) ===")
print("Как сейчас       плюс —       500к —       дно (—)    всего —   кл ~64  2029 —      касса29 -26.3")
print("Докрученная      плюс окт-27  500к апр-29  дно -5.3   всего 8.3 кл ~200 2029 +5.20  касса29  +2.7")
print("+ Форсаж         плюс апр-27  500к фев-28  дно -3.9   всего 6.9         2029 —      касса29  +8.2")
print("Мечта жизнь 6    плюс мар-27  дно -3.7                всего 6.7         2029 +6.50  касса29 +10.1")

print("\n=== чувствительность: рычаг «покупателей/мес» на Докрученной ===")
for b in (16, 21, 26, 31, 36):
    s={**DOKR,'buyers':b}
    run(f"  покупателей {b}", s)
