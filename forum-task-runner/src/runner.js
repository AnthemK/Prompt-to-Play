import './env.js';
import { chromium } from 'playwright';
import { existsSync } from 'node:fs';
import { TaskError, periodKey, isDue } from './model.js';
export class Runner {
  constructor(store, options={}) { this.store=store;this.options=options;this.locks=new Set();this.logins=new Map();this.pending=new Set();this.stopping=false; }
  busy(account) {return this.locks.has(account);}
  async context(task, login=false) {
    let browser;
    try {const edge = process.platform === 'darwin' && existsSync('/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge');
      const channel = process.env.FORUM_BROWSER_CHANNEL || (!existsSync(chromium.executablePath()) && edge ? 'msedge' : undefined);
      browser=await chromium.launch({channel,headless: login ? (this.options.loginHeadless === true) : !task.headed});} catch {throw new TaskError('browser');}
    try {
      const context=await browser.newContext({storageState:this.store.state(task.account),serviceWorkers:'block',acceptDownloads:false,ignoreHTTPSErrors:false});
      context.setDefaultTimeout(this.options.timeout || 15000);
      const allowed = url => {try {return task.origins.includes(new URL(url).origin);} catch {return false;}};
      await context.route('**/*',route=>allowed(route.request().url())?route.continue():route.abort('blockedbyclient'));
      await context.routeWebSocket('**/*',ws=>ws.close());
      return {browser,context,allowed,page:await context.newPage()};
    } catch(e) {await browser.close();throw e;}
  }
  async visible(page,selector) {return !!selector && await page.locator(selector).first().isVisible();}
  async save(context,account) {this.store.saveState(account,await context.storageState({indexedDB:true}));}
  async login(task) {
    if (this.stopping || this.busy(task.account)) throw new TaskError('busy');
    this.locks.add(task.account);
    let session;
    try {
      session=await this.context(task,true); session.task=task;
      await session.page.goto(task.login,{waitUntil:'domcontentloaded'});
      session.timer=setTimeout(()=>this.closeLogin(task.account).catch(()=>{}),10*60*1000);session.timer.unref();
      this.logins.set(task.account,session);
      session.browser.on('disconnected',()=>{if(this.logins.get(task.account)===session){clearTimeout(session.timer);this.logins.delete(task.account);this.locks.delete(task.account);}});
    } catch(e) {await session?.browser.close();this.locks.delete(task.account);throw e;}
  }
  async finishLogin(account) {
    const s=this.logins.get(account);if(!s) throw new TaskError('needs_login');
    if (!s.allowed(s.page.url()) || !await this.visible(s.page,s.task.authSelector)) throw new TaskError('needs_login');
    await this.save(s.context,account);await this.closeLogin(account);
  }
  async closeLogin(account) {const s=this.logins.get(account);if(!s)return;clearTimeout(s.timer);this.logins.delete(account);try{await s.browser.close();}finally{this.locks.delete(account);}}
  run(task, options={}) {
    const promise=this.execute(task,options);this.pending.add(promise);promise.finally(()=>this.pending.delete(promise)).catch(()=>{});return promise;
  }
  async execute(task,{force=false,now=new Date()}={}) {
    if(this.stopping || this.busy(task.account)) throw new TaskError('busy');
    const period=periodKey(task,now);
    if(this.store.completed(task.id,period)) return {status:'already_done'};
    if(this.store.uncertain(task.id) && !force) throw new TaskError('unknown');
    this.locks.add(task.account);
    if(force)this.store.resolve(task.id);
    const id=this.store.start(task.id,period);let session;let mutated=false;let status='failed';
    try {
      session=await this.context(task);const {page,context,allowed}=session;
      await page.goto(task.entry,{waitUntil:'domcontentloaded'});
      await page.locator(task.authSelector).first().waitFor({timeout:this.options.timeout || 10000}).catch(()=>{});
      if(await this.visible(page,task.challengeSelector)) throw new TaskError('needs_human');
      if(!await this.visible(page,task.authSelector)) throw new TaskError('needs_login');
      if(await this.visible(page,task.doneSelector)) status='already_done';
      else {
        for(let i=0;i<task.steps.length;i++) {
          const step=task.steps[i];this.store.step(id,i);
          if(await this.visible(page,task.challengeSelector))throw new TaskError('needs_human');
          if(step.skipIf && await this.visible(page,step.skipIf))continue;
          if(step.type==='goto')await page.goto(step.url,{waitUntil:'domcontentloaded'});
          if(step.type==='wait')await page.locator(step.selector).first().waitFor({state:'visible'});
          if(step.type==='fill') {
            const locator=page.locator(step.selector).first();
            if(await locator.getAttribute('type')==='password')throw new TaskError('invalid');
            await locator.fill(step.value);
          }
          if(step.type==='click') {mutated=true;await page.locator(step.selector).first().click();}
          if(step.type==='request') {
            if(!allowed(step.url))throw new TaskError('blocked');
            if(step.method==='POST')mutated=true;
            const r=await context.request.fetch(step.url,{method:step.method,data:step.data,maxRedirects:0,maxRetries:0,timeout:this.options.timeout || 15000});
            // Never forward cookies, headers or POST bodies through automatic redirects.
            if(r.status()>=300 && r.status()<400)throw new TaskError('blocked');
            if([401,403].includes(r.status()))throw new TaskError('needs_login');
            if(!r.ok())throw new TaskError('failed');
            await r.dispose();
          }
        }
        await page.locator(task.doneSelector).first().waitFor({state:'visible'});
        status='success';
      }
      await this.save(context,task.account);
    } catch(e) {
      status=mutated?'unknown':(e instanceof TaskError?e.code:'failed');
      // Save rotated authentication even when a later step fails; never save trace or page bodies.
      if(session)await this.save(session.context,task.account).catch(()=>{});
    } finally {
      try {await session?.browser.close();} finally {this.store.finish(id,status);this.locks.delete(task.account);}
    }
    return {id,status};
  }
  async tick(now=new Date()) {
    if(this.stopping)return;
    for(const task of this.store.tasks()) {
      if(isDue(task,now) && !this.busy(task.account) && !this.store.uncertain(task.id) && !this.store.attempted(task.id,periodKey(task,now))) await this.run(task,{now});
    }
  }
  async close() {this.stopping=true;await Promise.all([...this.logins.keys()].map(x=>this.closeLogin(x)));await Promise.allSettled([...this.pending]);}
}
