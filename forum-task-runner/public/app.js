const $=s=>document.querySelector(s);
let token=location.hash.slice(1) || sessionStorage.getItem('local-token') || '';
if(location.hash){sessionStorage.setItem('local-token',token);history.replaceState(null,'','/');}
let state={tasks:[],runs:[]};let editing=null;
const labels={success:'已完成',already_done:'已完成，无需操作',running:'执行中',needs_login:'需要登录',needs_human:'需要人工验证',unknown:'结果未知，需检查',reviewed:'已人工确认重试',failed:'执行失败',browser:'浏览器未就绪',blocked:'请求被拦截',invalid:'配置需要检查'};
async function api(url,data){const r=await fetch(url,{method:data?'POST':'GET',headers:{Authorization:'Bearer '+token,...(data?{'Content-Type':'application/json'}:{})},...(data?{body:JSON.stringify(data)}:{})});const value=await r.json();if(!r.ok)throw Error(value.error);return value;}
const notice=text=>{$('#notice').textContent=text;};
function el(tag,text,className){const e=document.createElement(tag);e.textContent=text;if(className)e.className=className;return e;}
function button(text,action,quiet=false,disabled=false){const b=el('button',text,quiet?'quiet':'');b.disabled=disabled;b.onclick=async()=>{b.disabled=true;try{await action();await refresh();}catch(e){notice(e.message);}finally{b.disabled=false;}};return b;}
function configOf(t){const {authenticated,busy,loginOpen,...config}=t;return config;}
async function refresh(){state=await api('/api/state');render();}
function render(){
 $('#tasks').replaceChildren();
 if(!state.tasks.length)$('#tasks').append(el('div','还没有任务。添加流程后，先登录并手动试运行。','empty'));
 for(const t of state.tasks){
  const c=el('article','','card');c.append(el('h3',t.name),el('div',new URL(t.entry).host,'origin'));
  const s=t.schedule;const latest=state.runs.find(r=>r.task===t.id);
  c.append(el('div',`${t.authenticated?'已保存登录状态（有效性在运行时检查）':'尚未保存登录状态'}\n${s.enabled?'自动执行':'计划暂停'} · ${s.kind==='daily'?'每天':'每周'+['','一','二','三','四','五','六','日'][s.weekday]} ${s.time} · ${s.timezone}${latest?'\n最近：'+(labels[latest.status] || latest.status):''}`,'meta'));
  c.querySelector('.meta').style.whiteSpace='pre-line';
  const a=el('div','','actions');
  a.append(button('立即运行',async()=>{const unknown=state.runs.some(r=>r.task===t.id&&r.status==='unknown');if(unknown&&!confirm('上次提交结果不确定。请先在网站核对，确认可以重新执行后继续。'))return;notice('正在执行，请稍候…');const r=await api('/api/run',{id:t.id,confirmRetry:unknown});notice(labels[r.status] || r.status);},false,t.busy));
  if(t.loginOpen){a.append(button('登录完成，保存',async()=>{await api('/api/login/save',{id:t.id});notice('登录状态已加密保存在本机。');}),button('取消登录',()=>api('/api/login/cancel',{id:t.id}),true));}
  else a.append(button('登录',async()=>{notice('正在打开独立浏览器，请在该窗口完成登录。');await api('/api/login',{id:t.id});notice('在浏览器完成登录后，回到这里点击“登录完成，保存”。窗口最多保留 10 分钟。');},true,t.busy));
  a.append(button(s.enabled?'暂停计划':'启用计划',async()=>{const config=configOf(t);config.schedule.enabled=!s.enabled;await api('/api/tasks',config);},true,t.busy));
  a.append(button('编辑',()=>openEditor(t),true,t.busy));
  a.append(button('清除登录',async()=>{if(confirm('清除该账号保存的登录状态？'))await api('/api/auth/clear',{id:t.id});},true,t.busy));c.append(a);$('#tasks').append(c);
 }
 $('#runs').replaceChildren();
 if(!state.runs.length){const tr=el('tr');const td=el('td','暂无执行记录');td.colSpan=4;tr.append(td);$('#runs').append(tr);}
 for(const r of state.runs){const tr=el('tr');tr.append(el('td',state.tasks.find(t=>t.id===r.task)?.name || r.task),el('td',new Date(r.started).toLocaleString('zh-CN')),el('td',labels[r.status] || r.status,['success','already_done'].includes(r.status)?'good':'warn'),el('td',r.step<0?'检查状态':String(r.step+1)));$('#runs').append(tr);}
}
function openEditor(task){editing=task?.id || null;$('#config').value=JSON.stringify(task?configOf(task):{id:'my-forum',name:'我的论坛',account:'my-forum-main',origins:['https://forum.example.com'],entry:'https://forum.example.com/checkin',login:'https://forum.example.com/login',authSelector:'[data-user]',doneSelector:'[data-checkin-done]',challengeSelector:'',headed:false,schedule:{enabled:false,kind:'daily',time:'09:00',weekday:1,timezone:'Asia/Shanghai',windowHours:12},steps:[{type:'click',selector:'button#checkin',skipIf:'[data-checkin-done]'}]},null,2);$('#form-error').textContent='';$('#editor').showModal();}
$('#add').onclick=()=>openEditor();$('#close').onclick=()=>$('#editor').close();
$('#task-form').onsubmit=async e=>{e.preventDefault();try{const t=JSON.parse($('#config').value);if(editing&&t.id!==editing)throw Error('编辑时请保留任务 id。');await api('/api/tasks',t);$('#editor').close();await refresh();notice('任务已保存。首次接入请先登录并试运行。');}catch(e){$('#form-error').textContent=e.message;}};
refresh().catch(e=>notice(e.message));setInterval(()=>refresh().catch(()=>{}),4000);
