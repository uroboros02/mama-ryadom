const fs = require('fs');
const html = fs.readFileSync('/Users/nikolaymacbook/Claude/mama-ryadom-bot/finmodel/finmodel-trenazher.html', 'utf8');
const code = html.split("'use strict';")[1].split('/* ===== ФОРМАТЫ')[0];
const report = `
for (const name of Object.keys(PRESETS)) {
  const r = simulate(PRESETS[name], true);
  const y29 = r.pnl.reduce((a, b, i) => i >= 29 ? a + b : a, 0);
  const be = breakeven(PRESETS[name], true);
  console.log([name, r.cash[40].toFixed(4), r.A[40].toFixed(6), y29.toFixed(4), be].join(' | '));
}`;
eval(code + report);
