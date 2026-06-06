#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сборка лид-выборки из сырой выгрузки переписок Wazzup.

Вход :  chats wazzup.csv          (в корне репо; ПД — НЕ коммитится, см. .gitignore)
Выход:  data/leads-filtered.md    (ПД-маскирован, но тоже НЕ коммитится)

Логика (см. docs/wazzup-corpus-analysis.md):
  • Лид-намерение ловим ТОЛЬКО во входящих (слова клиента) — наши исходящие
    приглашения «на пробное» сюда не считаются, иначе лидом станет каждый чат.
  • «Действующий клиент» отсекаем по сервисным маркерам в ЛЮБУЮ сторону
    (справка/долг/разряд/личный кабинет/продление) — если мы шлём человеку
    такое, он уже клиент, а не лид.
  • Tier 1 «чистые лиды»  = есть лид-сигнал, нет ops-сигнала.
  • Tier 2 «лид→клиент»   = есть и лид-, и ops-сигнал (виден лид-участок).

Запуск:  python3 scripts/filter_leads.py
Перезапускать после любой новой/полной выгрузки — выборка пересобирается с нуля.
"""
import csv, re, os, statistics
from collections import defaultdict

SRC = 'chats wazzup.csv'
OUT = 'data/leads-filtered.md'
csv.field_size_limit(10**7)

# LEAD — намерение КЛИЕНТА (искать только во входящих)
LEAD = [re.compile(p, re.I) for p in [
    r'(интересует (гимнастик|балет|сенсорик|занят|секци|растяж)|хоч[уим]+ .*(записать|попробовать|привести|на пробн)|можно (ли )?записа|запишите (нас|меня|ребёнк|ребенк)|хотел[аи]? бы (записать|попробовать|привести)|примете ли|возьм[её]те ли)',
    r'(сколько стоит|стоимость абонемент|стоимость занят|какая стоимость|сколько за занят)',
    r'(с какого возраста|со скольки лет|подойд[её]т ли|подходит ли (нам|для)|нам \d{1,2} год|ребёнку \d{1,2} (лет|год)|ребенку \d{1,2} (лет|год)|дочке? \d|сыну \d)',
    r'(на пробн|пробное занят|первое занят|хотим попроб)',
]]
# OPS — признак ДЕЙСТВУЮЩЕГО клиента (искать в обоих направлениях)
OPS = [re.compile(p, re.I) for p in [
    r'(в кабинете|личн\w* кабинет|не отображ|не вижу расписан|восстановлени\w* доступ)',
    r'(возврат налог|налогов\w* вычет|квитанц|справк\w* для налог)',
    r'(разряд|первенств|соревнован|выступлен|турнир|фазенд|медал|\d{4} ?г\.?р)',
    r'(тренер\w* (уволил|назнач|заменя|поменя)|какого тренера)',
    r'(продл\w* абонемент|заморозить абонемент|остаток занят)',
    r'(оригинал справк|справка готов|медсправк|срок медицинск\w* справк|заканчивается срок мед)',
    r'(задолжен|наличии задолжен|оплатите до|оргвзнос|напоминаем вам, что)',
]]

def hit(text, res):
    return any(r.search(text) for r in res)

EMAIL = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
DIGITS = re.compile(r'\d{6,}')
AUTO = re.compile(r'^Здравствуйте! Сейчас мы отдыхаем')
AUTO2 = re.compile(r'^Здравствуйте! Спасибо, что написали')

def mask(t):
    t = EMAIL.sub('[email]', t)
    t = DIGITS.sub('[номер]', t)
    return re.sub(r'\s+', ' ', t).strip()

def main():
    chat_rows = defaultdict(list)
    with open(SRC, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            chat_rows[row['chat_id']].append(row)

    tier1, tier2 = [], []
    for cid, rows in chat_rows.items():
        has_lead = any(r['direction'] == 'inbound' and hit((r['text'] or ''), LEAD) for r in rows)
        has_ops = any(hit((r['text'] or ''), OPS) for r in rows)
        if has_lead and not has_ops:
            tier1.append(cid)
        elif has_lead and has_ops:
            tier2.append(cid)

    def render(cid, cap):
        rows = list(reversed(chat_rows[cid]))  # файл идёт новые→старые → разворот в хронологию
        lines, pay = [], False
        for r in rows:
            t = (r['text'] or '').strip()
            who = 'КЛИЕНТ' if r['direction'] == 'inbound' else 'МЫ'
            if not t and r['file_url'].strip():
                body = '[медиа]'
            elif AUTO.match(t) or AUTO2.match(t):
                body = '[автоответ]'
            else:
                body = mask(t)
            if not body:
                continue
            if re.search(r'(спасибо за оплату|создала вам личный кабинет)', body, re.I) or \
               (who == 'КЛИЕНТ' and re.search(r'\bоплатил', body, re.I)):
                pay = True
            lines.append(f"{who}: {body}")
        extra = 0
        if len(lines) > cap:
            extra = len(lines) - cap
            lines = lines[:cap]
        return lines, extra, pay

    def section(fh, title, cids, cap):
        fh.write(f"\n\n{'=' * 70}\n## {title} — {len(cids)} диалогов\n{'=' * 70}\n")
        lens = []
        for i, cid in enumerate(sorted(cids, key=lambda c: len(chat_rows[c])), 1):
            lines, extra, pay = render(cid, cap)
            lens.append(len(lines))
            tag = ' [есть сигнал оплаты]' if pay else ''
            fh.write(f"\n### Диалог {i} · •••{cid[-4:]} · {len(lines) + extra} реплик{tag}\n")
            fh.write('\n'.join('  ' + l for l in lines))
            if extra:
                fh.write(f"\n  … (ещё {extra} реплик — операционка, обрезано)")
            fh.write('\n')
        return lens

    os.makedirs('data', exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write("# Лид-выборка из переписок Wazzup (отфильтровано)\n\n")
        fh.write("Производное от `chats wazzup.csv` (разбор — `docs/wazzup-corpus-analysis.md`).\n")
        fh.write("Пересобрать: `python3 scripts/filter_leads.py`. ПД-файл — в git не коммитим.\n")
        l1 = section(fh, "ЧИСТЫЕ ЛИДЫ (намерение клиента, без операционки)", tier1, 80)
        l2 = section(fh, "СМЕШАННЫЕ (лид → стал клиентом; виден лид-участок)", tier2, 50)

    print(f"Tier1 чистые лиды: {len(tier1)} (медиана {int(statistics.median(l1))} реплик)")
    print(f"Tier2 смешанные:   {len(tier2)} (медиана {int(statistics.median(l2))} реплик)")
    print(f"→ {OUT} ({os.path.getsize(OUT) // 1024} КБ)")


if __name__ == '__main__':
    main()
