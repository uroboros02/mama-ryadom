// Функциональный тест тренажёра без браузера: DOM-заглушка + реальный скрипт страницы
const fs = require('fs');
const html = fs.readFileSync('/Users/nikolaymacbook/Claude/mama-ryadom-bot/finmodel/finmodel-trenazher.html','utf8');
const src = html.split('<script>')[1].split('</script>')[0];

class El {
  constructor(id){ this.id=id||''; this._h={}; this.value=''; this.textContent=''; this._html='';
    this.style={}; this.dataset={}; this.children=[];
    this.classList={toggle(){},add(){},remove(){}}; this.checked=true; }
  set innerHTML(v){ this._html=v; } get innerHTML(){ return this._html; }
  addEventListener(t,f){ (this._h[t]=this._h[t]||[]).push(f); }
  fire(t,ev){ (this._h[t]||[]).forEach(f=>f(ev||{})); }
  appendChild(c){ this.children.push(c); return c; }
  querySelector(){ return new El('q'); }
  querySelectorAll(){ const a=[new El('q0'),new El('q1'),new El('q2'),new El('q3')]; a.forEach=Array.prototype.forEach.bind(a); return a; }
  insertAdjacentHTML(){}
  setAttribute(){}
  getBoundingClientRect(){ return {left:0,top:0,width:720,height:250}; }
}
const reg = {};
const doc = {
  getElementById(id){ return reg[id] || (reg[id]=new El(id)); },
  createElement(tag){ return new El(tag); },
};

new Function('document', src)(doc);   // страница «загрузилась»: init с пресетом Докрученная

console.log('старт (пресет Докрученная): номин =', reg['in_nomin'].value, '/', reg['v_nomin'].textContent);

// дёргаем ползунок «8 занятий» на 50
const m8 = reg['in_m8']; m8.value='50'; m8.fire('input');
console.log('после m8→50: номин =', reg['in_nomin'].value, '/', reg['v_nomin'].textContent);
console.log('строка микса:', reg['mixInfo'].textContent);

// и ещё один: единый-12 на 20
const mu12 = reg['in_mu12']; mu12.value='20'; mu12.fire('input');
console.log('после mu12→20: номин =', reg['in_nomin'].value, '/', reg['v_nomin'].textContent);
console.log('строка микса:', reg['mixInfo'].textContent);

// связка отток ↔ жизнь
const churn = reg['in_churn']; churn.value='20'; churn.fire('input');
console.log('\nотток→20%: жизнь =', reg['in_life'].value, '/', reg['v_life'].textContent);
console.log('строка оттока:', reg['churnInfo'].textContent);
const life = reg['in_life']; life.value='3'; life.fire('input');
console.log('жизнь→3: отток =', reg['in_churn'].value, '/', reg['v_churn'].textContent);
console.log('строка оттока:', reg['churnInfo'].textContent);

// предпродажа
const se75 = reg['in_se75']; se75.value='15'; se75.fire('input');
const se50 = reg['in_se50']; se50.value='20'; se50.fire('input');
console.log('\nпредпродажа 15+20:', reg['preInfo'].textContent);
