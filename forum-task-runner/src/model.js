export class TaskError extends Error {
  constructor(code) { super(code); this.code = code; }
}
export const messages = {
  invalid: '配置不合法，请检查网址、选择器及计划。', blocked: '请求被站点访问范围限制拦截。',
  needs_login: '登录已失效，请打开登录窗口重新登录。', needs_human: '需要人工处理，请打开登录窗口。',
  failed: '步骤未完成或页面已变化，请检查站点流程。', unknown: '提交结果尚未确认，请检查网站后再决定是否重试。',
  busy: '该账号已有任务或登录窗口在使用。', browser: '浏览器无法启动，请先安装 Chromium。',
  success: '已核实任务完成。', already_done: '已完成，无需重复操作。', cancelled: '已取消。',
};
export function originOf(value, local = false) {
  let u; try { u = new URL(value); } catch { throw new TaskError('invalid'); }
  if (u.username || u.password || !(['https:'].includes(u.protocol) || (local && u.protocol === 'http:' && u.hostname === '127.0.0.1'))) throw new TaskError('invalid');
  return u.origin;
}
export function validateTask(input, local = false) {
  if (!input || typeof input !== 'object') throw new TaskError('invalid');
  const t = structuredClone(input);
  if (!/^[a-z0-9_-]{1,60}$/.test(t.id || '') || !/^[a-z0-9_-]{1,60}$/.test(t.account || '') || typeof t.name !== 'string' || !t.name.trim() || t.name.length > 80) throw new TaskError('invalid');
  if (!Array.isArray(t.origins) || !t.origins.length || t.origins.length > 15) throw new TaskError('invalid');
  t.origins = [...new Set(t.origins.map(x => { if (originOf(x, local) !== x) throw new TaskError('invalid'); return x; }))];
  for (const key of ['entry', 'login']) if (!t.origins.includes(originOf(t[key], local))) throw new TaskError('invalid');
  for (const key of ['authSelector', 'doneSelector']) if (typeof t[key] !== 'string' || !t[key] || t[key].length > 500) throw new TaskError('invalid');
  if (t.challengeSelector && (typeof t.challengeSelector !== 'string' || t.challengeSelector.length > 500)) throw new TaskError('invalid');
  const s = t.schedule;
  if (!s || !['daily', 'weekly'].includes(s.kind) || !/^([01]\d|2[0-3]):[0-5]\d$/.test(s.time) || !Number.isInteger(s.weekday) || s.weekday < 1 || s.weekday > 7 || !Number.isInteger(s.windowHours) || s.windowHours < 1 || s.windowHours > 24 || typeof s.enabled !== 'boolean') throw new TaskError('invalid');
  try { new Intl.DateTimeFormat('en', { timeZone: s.timezone }).format(); } catch { throw new TaskError('invalid'); }
  if (typeof s.timezone !== 'string') throw new TaskError('invalid');
  if (!Array.isArray(t.steps) || !t.steps.length || t.steps.length > 40) throw new TaskError('invalid');
  for (const step of t.steps) {
    if (!['goto','click','fill','wait','request'].includes(step.type)) throw new TaskError('invalid');
    if (['click','fill','wait'].includes(step.type) && (typeof step.selector !== 'string' || !step.selector || step.selector.length > 500)) throw new TaskError('invalid');
    if (step.skipIf && (typeof step.skipIf !== 'string' || step.skipIf.length > 500)) throw new TaskError('invalid');
    if (['goto','request'].includes(step.type) && !t.origins.includes(originOf(step.url, local))) throw new TaskError('invalid');
    if (step.type === 'fill' && (typeof step.value !== 'string' || step.value.length > 2000)) throw new TaskError('invalid');
    if (step.type === 'request' && !['GET','POST'].includes(step.method)) throw new TaskError('invalid');
    if (step.type === 'request' && step.headers) throw new TaskError('invalid');
  }
  // Explicit schema: do not persist extra fields such as passwords or custom headers.
  const steps = t.steps.map(x => Object.fromEntries(['type','selector','value','url','method','data','skipIf'].filter(k=> x[k] !== undefined).map(k=>[k,x[k]])));
  return {id:t.id,name:t.name.trim(),account:t.account,origins:t.origins,entry:t.entry,login:t.login,authSelector:t.authSelector,doneSelector:t.doneSelector,challengeSelector:t.challengeSelector || '',headed: t.headed === true,schedule:{enabled:s.enabled,kind:s.kind,time:s.time,weekday:s.weekday,timezone:s.timezone,windowHours:s.windowHours},steps};
}
export function clockParts(now, zone) {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(now).map(x=>[x.type,x.value]));
  const date = `${p.year}-${p.month}-${p.day}`;
  const day = new Date(`${date}T00:00:00Z`);
  const weekday = day.getUTCDay() || 7;
  day.setUTCDate(day.getUTCDate() - weekday + 1);
  return {date, week:day.toISOString().slice(0,10), weekday, minute:Number(p.hour)*60+Number(p.minute)};
}
export function periodKey(task, now = new Date()) {
  const p = clockParts(now, task.schedule.timezone);
  return `${task.schedule.kind}:${task.schedule.kind === 'daily' ? p.date : p.week}`;
}
export function isDue(task, now = new Date()) {
  const s = task.schedule; if (!s.enabled) return false;
  const p = clockParts(now,s.timezone);
  const [h,m]=s.time.split(':').map(Number);
  const elapsed = (s.kind === 'weekly' ? (p.weekday-s.weekday)*1440 : 0) + p.minute-h*60-m;
  return elapsed >= 0 && elapsed < s.windowHours*60;
}
