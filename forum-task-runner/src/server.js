import './env.js';
import http from 'node:http';
import { readFileSync, mkdirSync, openSync, closeSync, unlinkSync, writeFileSync, existsSync } from 'node:fs';
import { join,resolve } from 'node:path';
import { randomBytes, timingSafeEqual } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { Store } from './store.js';
import { Runner } from './runner.js';
import { validateTask,TaskError,messages } from './model.js';
import { projectDir } from './env.js';
import { startDemo,demoTask } from './demo.js';
const assets={'/':['index.html','text/html'],'/app.js':['app.js','text/javascript'],'/style.css':['style.css','text/css']};
async function body(req) {
  let value='';for await(const part of req){value+=part;if(Buffer.byteLength(value)>32768)throw new TaskError('invalid');}
  try{return JSON.parse(value || '{}');}catch{throw new TaskError('invalid');}
}
export async function createApp({dir=join(projectDir,'.data'),port=8924,demo=false,runnerOptions={},schedule=true}={}) {
  mkdirSync(dir,{recursive:true,mode:0o700});
  const lockFile=join(dir,'service.lock');let lock;
  try{lock=openSync(lockFile,'wx',0o600);writeFileSync(lock,String(process.pid));}catch{
    if(existsSync(lockFile)){const pid=Number(readFileSync(lockFile,'utf8'));let alive=true;try{process.kill(pid,0);}catch(e){if(e.code==='ESRCH')alive=false;}if(!alive){unlinkSync(lockFile);lock=openSync(lockFile,'wx',0o600);writeFileSync(lock,String(process.pid));}}
    if(lock===undefined)throw Error('已有服务在运行，或锁文件需要人工检查。');
  }
  const store=new Store(dir),runner=new Runner(store,runnerOptions),token=randomBytes(32).toString('hex');
  let fixture;let origin;let timer;let ticking=false;
  const server=http.createServer(async(req,res)=>{
    res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','no-referrer');
    res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'");
    const json=(status,value)=>{res.writeHead(status,{'Content-Type':'application/json; charset=utf-8'});res.end(JSON.stringify(value));};
    try {
      if(req.headers.host!==new URL(origin).host){json(403,{error:'拒绝未知 Host'});return;}
      if(req.headers.origin && req.headers.origin!==origin){json(403,{error:'拒绝跨域访问'});return;}
      if(assets[req.url] && req.method==='GET'){const [file,type]=assets[req.url];res.writeHead(200,{'Content-Type':type+'; charset=utf-8'});res.end(readFileSync(join(projectDir,'public',file)));return;}
      const auth=req.headers.authorization || '';const expected='Bearer '+token;
      if(auth.length!==expected.length || !timingSafeEqual(Buffer.from(auth),Buffer.from(expected))){json(401,{error:'请使用启动时显示的本地访问链接。'});return;}
      if(req.method!=='GET' && req.headers.origin!==origin){json(403,{error:'缺少本地请求来源'});return;}
      if(req.method==='GET' && req.url==='/api/state'){
        json(200,{tasks:store.tasks().map(t=>({...t,authenticated:!!store.state(t.account),busy:runner.busy(t.account),loginOpen:runner.logins.has(t.account)})),runs:store.runs(),demo:!!fixture});return;
      }
      if(req.method!=='POST'){json(404,{error:'不存在'});return;}
      if(!(req.headers['content-type'] || '').startsWith('application/json'))throw new TaskError('invalid');
      const data=await body(req);
      if(req.url==='/api/tasks') {
        const task=validateTask(data,!!fixture);const old=store.task(task.id);
        if((old && runner.busy(old.account)) || runner.busy(task.account))throw new TaskError('busy');
        if(store.tasks().some(t=>t.id!==task.id && t.account===task.account && [...t.origins].sort().join()!==[...task.origins].sort().join()))throw new TaskError('invalid');
        store.saveTask(task);json(200,{ok:true});return;
      }
      const task=store.task(data.id);if(!task)throw new TaskError('invalid');
      if(req.url==='/api/run') {json(200,await runner.run(task,{force:data.confirmRetry===true}));return;}
      if(req.url==='/api/login'){await runner.login(task);json(200,{ok:true});return;}
      if(req.url==='/api/login/save'){await runner.finishLogin(task.account);json(200,{ok:true});return;}
      if(req.url==='/api/login/cancel'){await runner.closeLogin(task.account);json(200,{ok:true});return;}
      if(req.url==='/api/auth/clear'){if(runner.busy(task.account))throw new TaskError('busy');store.clearState(task.account);json(200,{ok:true});return;}
      json(404,{error:'不存在'});
    }catch(e){const code=e instanceof TaskError?e.code:'failed';json(400,{code,error:messages[code] || messages.failed});}
  });
  try {
    if(demo){fixture=await startDemo(port===0?0:8925);const task=demoTask(fixture.origin);if(!store.task(task.id))store.saveTask(task);}
    await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(port,'127.0.0.1',resolve);});origin=`http://127.0.0.1:${server.address().port}`;
  }catch(e){await fixture?.close();store.close();closeSync(lock);unlinkSync(lockFile);throw e;}
  const tick=async()=>{if(ticking)return;ticking=true;try{await runner.tick();}catch{}finally{ticking=false;}};
  if(schedule){timer=setInterval(tick,30000);timer.unref();void tick();}
  return {server,store,runner,token,origin,fixture,async close(){clearInterval(timer);await runner.close();await new Promise(r=>server.close(r));await fixture?.close();store.close();closeSync(lock);unlinkSync(lockFile);}};
}
if(process.argv[1] && import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
  let app;try{app=await createApp({demo:process.argv.includes('--demo')});console.log(`本地任务工具已启动：${app.origin}/#${app.token}\n仅本机访问；Ctrl+C 停止。`);}
  catch{console.error('启动失败：请检查端口 8924/8925、运行环境和 .data/service.lock。');process.exitCode=1;}
  if(app){let closing=false;for(const sig of ['SIGINT','SIGTERM'])process.on(sig,async()=>{if(closing)return;closing=true;await app.close();process.exit(0);});}
}
