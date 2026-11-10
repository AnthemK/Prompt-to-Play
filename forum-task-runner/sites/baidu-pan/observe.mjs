import { chromium } from 'playwright';
import { existsSync } from 'node:fs';

// Only summarize request paths and status codes; never record headers, bodies or queries.
const edge = '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge';
const browser = await chromium.launch({ headless: false, channel: !existsSync(chromium.executablePath()) && existsSync(edge) ? 'msedge' : undefined });
const context = await browser.newContext({ acceptDownloads: false });
const page = await context.newPage();
page.on('response', response => {
  const req = response.request();
  if (!['xhr', 'fetch'].includes(req.resourceType())) return;
  const url = new URL(response.url());
  if (!(url.hostname === 'baidu.com' || url.hostname.endsWith('.baidu.com'))) return;
  process.stdout.write(JSON.stringify({ method: req.method(), host: url.hostname, path: url.pathname, status: response.status() }) + '\n');
});
await page.goto('https://pan.baidu.com/buy/memberCenter?tag=8&from=homepage#/svip', { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(() => {});
process.stdout.write('READY: 请在窗口中登录；暂时不要点击签到。\n');
await new Promise(resolve => browser.on('disconnected', resolve));
