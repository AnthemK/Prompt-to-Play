import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync,readFileSync,mkdirSync} from 'node:fs';
import https from 'node:https';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createApp} from '../src/server.js';
import {demoTask} from '../src/demo.js';
async function setup(){const dir=mkdtempSync(join(tmpdir(),'forum-app-'));const app=await createApp({dir,port:0,demo:true,schedule:false,runnerOptions:{loginHeadless:true,timeout:1200}});return {app,dir,async close(){await app.close();rmSync(dir,{recursive:true,force:true});}};}
async function login(app,t){await app.runner.login(t);const s=app.runner.logins.get(t.account);await s.page.getByRole('button',{name:'模拟登录'}).click();await s.page.locator('[data-auth]').waitFor();await app.runner.finishLogin(t.account);}
test('real browser: login, cookie rotation, dedupe and shared request cookies',async()=>{
 const env=await setup();const {app}=env;
 try{const t=app.store.tasks()[0];assert.equal((await app.runner.run(t)).status,'needs_login');await login(app,t);
 const old=app.store.state(t.account).cookies.find(c=>c.name==='session').value;
 assert.equal((await app.runner.run(t)).status,'success');
 const fresh=app.store.state(t.account).cookies.find(c=>c.name==='session').value;assert.notEqual(old,fresh);
 assert.equal((await app.runner.run(t)).status,'already_done');assert.equal(app.fixture.submissions(),1);
 const reward={...t,id:'demo-reward',doneSelector:'[data-reward]',steps:[{type:'request',method:'POST',url:app.fixture.origin+'/reward'},{type:'goto',url:app.fixture.origin+'/'}]};
 app.store.saveTask(reward);assert.equal((await app.runner.run(reward)).status,'success');
 const check={...t,id:'check-state'};app.store.saveTask(check);assert.equal((await app.runner.run(check)).status,'already_done');
 app.fixture.expire();const expired={...t,id:'expired'};app.store.saveTask(expired);assert.equal((await app.runner.run(expired)).status,'needs_login');
 }finally{await env.close();}
});
test('unknown post-submit state stops scheduler; redirect destinations are not followed',async()=>{
 const env=await setup();const {app}=env;
 try{const t=app.store.tasks()[0];await login(app,t);const broken={...t,id:'broken',doneSelector:'[never-appears]'};app.store.saveTask(broken);
 assert.equal((await app.runner.run(broken)).status,'unknown');assert.equal(app.fixture.submissions(),1);
 await assert.rejects(app.runner.run(broken),e=>e.code==='unknown');
 const redirect={...t,id:'redirect',doneSelector:'[never-appears]',steps:[{type:'request',method:'GET',url:app.fixture.origin+'/redirect'}]};
 app.store.saveTask(redirect);assert.equal((await app.runner.run(redirect)).status,'blocked');
 const s=await app.runner.context(t);try{await assert.rejects(s.page.goto('http://127.0.0.1:1/blocked'));}finally{await s.browser.close();}
 }finally{await env.close();}
});
test('API authentication, origin checks, account lock and UI workflow',async()=>{
 const env=await setup();const {app}=env;
 try{
 assert.equal((await fetch(app.origin+'/api/state')).status,401);
 const headers={Authorization:'Bearer '+app.token,'Content-Type':'application/json',Origin:'https://evil.example'};
 assert.equal((await fetch(app.origin+'/api/tasks',{method:'POST',headers,body:'{}'})).status,403);
 headers.Origin=app.origin;assert.equal((await fetch(app.origin+'/api/tasks',{method:'POST',headers,body:'{}'})).status,400);
 const t=app.store.tasks()[0];await app.runner.login(t);await assert.rejects(app.runner.run(t),e=>e.code==='busy');await app.runner.closeLogin(t.account);
 await login(app,t);await app.runner.run(t);
 const session=await app.runner.context({...t,origins:[app.origin]});try{
 await session.page.goto(app.origin+'/#'+app.token);await session.page.getByRole('heading',{name:t.name}).waitFor();
 await session.page.getByRole('button',{name:'编辑',exact:true}).click();assert.equal(await session.page.locator('#editor').isVisible(),true);
 await session.page.getByRole('button',{name:'保存任务',exact:true}).click();await session.page.locator('#editor').waitFor({state:'hidden'});
 await session.page.getByRole('button',{name:'启用计划',exact:true}).click();await session.page.getByRole('button',{name:'暂停计划',exact:true}).waitFor();
 await session.page.getByRole('button',{name:'暂停计划',exact:true}).click();await session.page.getByRole('button',{name:'启用计划',exact:true}).waitFor();
 const output=fileURLToPath(new URL('../.test-output/',import.meta.url));mkdirSync(output,{recursive:true});await session.page.screenshot({path:join(output,'dashboard.png'),fullPage:true});
 }finally{await session.browser.close();}
 }finally{await env.close();}
});

test('scheduler starts once per business period and TLS rejects untrusted certificates',async()=>{
 const env=await setup();const {app}=env;
 let tls;
 try{
 const t=app.store.tasks()[0];await login(app,t);t.schedule.enabled=true;t.schedule.time='00:00';t.schedule.windowHours=24;app.store.saveTask(t);
 const now=new Date('2026-10-21T02:00:00Z');await app.runner.tick(now);await app.runner.tick(now);
 assert.equal(app.store.runs().length,1);assert.equal(app.store.runs()[0].status,'success');assert.equal(app.fixture.submissions(),1);
 let requests=0;
 execFileSync('openssl',['req','-x509','-newkey','rsa:2048','-nodes','-keyout',join(env.dir,'localhost.key'),'-out',join(env.dir,'localhost.crt'),'-days','1','-subj','/CN=localhost'],{stdio:'ignore'});
 tls=https.createServer({key:readFileSync(join(env.dir,'localhost.key')),cert:readFileSync(join(env.dir,'localhost.crt'))},(req,res)=>{requests++;res.end('unexpected');});
 await new Promise(r=>tls.listen(0,'127.0.0.1',r));
 const url=`https://127.0.0.1:${tls.address().port}`;
 const session=await app.runner.context({...t,origins:[url]});
 try{await assert.rejects(session.context.request.get(url));await assert.rejects(session.page.goto(url));assert.equal(requests,0);}finally{await session.browser.close();}
 }finally{if(tls)await new Promise(r=>tls.close(r));await env.close();}
});
