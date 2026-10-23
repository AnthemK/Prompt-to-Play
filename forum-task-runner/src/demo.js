import http from 'node:http';
import { randomUUID } from 'node:crypto';
export async function startDemo(port=8925) {
  const sessions=new Map();const users=new Map();let submissions=0;
  const server=http.createServer((req,res)=>{
    const sid=/session=([^;]+)/.exec(req.headers.cookie || '')?.[1]; const user=sessions.get(sid);
    res.setHeader('Cache-Control','no-store');
    const redirect=url=>{res.writeHead(303,{Location:url});res.end();};
    if(req.url==='/login' && req.method==='POST') {
      const id=randomUUID();const u={done:false,reward:false};sessions.set(id,u);users.set(id,u);
      res.setHeader('Set-Cookie',`session=${id}; HttpOnly; SameSite=Lax; Path=/`);redirect('/');return;
    }
    if(req.url==='/sign' && req.method==='POST') {
      if(!user){res.writeHead(401);res.end();return;}
      if(!user.done){submissions++;user.done=true;}
      const id=randomUUID();sessions.delete(sid);sessions.set(id,user);
      res.setHeader('Set-Cookie',`session=${id}; HttpOnly; SameSite=Lax; Path=/`);redirect('/');return;
    }
    if(req.url==='/reward' && req.method==='POST') {
      if(!user){res.writeHead(401);res.end();return;}
      user.reward=true;res.writeHead(200,{'Content-Type':'application/json'});res.end('{"ok":true}');return;
    }
    if(req.url==='/redirect') {res.writeHead(307,{Location:'http://127.0.0.1:1/forbidden'});res.end();return;}
    res.setHeader('Content-Type','text/html; charset=utf-8');
    res.end(`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>本地演示论坛</title><style>body{font:18px system-ui;max-width:620px;margin:80px auto;background:#f5f4ee;color:#263b35}button{padding:12px 20px;background:#24634f;color:white;border:0;border-radius:10px}section{background:white;padding:32px;border-radius:20px}</style><section><h1>本地演示论坛</h1><p>仅用于验证流程，不是真实论坛，不需要账号或密码。</p>${!user?'<form action="/login" method="post"><button>模拟登录</button></form>':`<p data-auth>已登录演示账号</p>${user.done?'<p data-done>今日签到已完成</p>':'<form action="/sign" method="post"><button id="sign">签到</button></form>'}${user.reward?'<p data-reward>奖励已领取</p>':'<p>待领取奖励</p>'}`}</section></html>`);
  });
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(port,'127.0.0.1',resolve);});
  return {server,origin:`http://127.0.0.1:${server.address().port}`,submissions:()=>submissions,expire:()=>sessions.clear(),close:()=>new Promise(r=>server.close(r))};
}
export function demoTask(origin) {return {id:'demo-checkin',name:'本地演示 · 每日签到',account:'demo',origins:[origin],entry:origin+'/',login:origin+'/login',authSelector:'[data-auth]',doneSelector:'[data-done]',challengeSelector:'',headed:false,schedule:{enabled:false,kind:'daily',time:'09:00',weekday:1,timezone:'Asia/Shanghai',windowHours:12},steps:[{type:'click',selector:'#sign',skipIf:'[data-done]'}]};}
