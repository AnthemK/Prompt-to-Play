import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync,readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {Store} from '../src/vault-store.js';
import {validateTask,isDue,periodKey} from '../src/model.js';
import {demoTask} from '../src/demo.js';
const task=()=>demoTask('http://127.0.0.1:9001');
test('schedule respects Shanghai calendar, weekly window and manual period identity',()=>{
 const t=task();t.schedule.enabled=true;
 assert.equal(isDue(t,new Date('2026-10-21T00:59:00Z')),false);
 assert.equal(isDue(t,new Date('2026-10-21T01:00:00Z')),true);
 assert.equal(isDue(t,new Date('2026-10-21T13:01:00Z')),false);
 assert.equal(periodKey(t,new Date('2026-10-20T18:00:00Z')),'daily:2026-10-21');
 t.schedule.kind='weekly';t.schedule.weekday=3;
 assert.equal(isDue(t,new Date('2026-10-21T02:00:00Z')),true);
 assert.equal(isDue(t,new Date('2026-10-22T02:00:00Z')),false);
 assert.equal(periodKey(t,new Date('2026-10-21T02:00:00Z')),'weekly:2026-10-19');
 t.schedule.timezone='America/New_York';t.schedule.kind='daily';t.schedule.time='09:00';
 assert.equal(isDue(t,new Date('2026-01-21T13:59:00Z')),false);
 assert.equal(isDue(t,new Date('2026-01-21T14:00:00Z')),true);
});
test('reject invalid origins, inline URL credentials and unapproved request destinations',()=>{
 const t=task();assert.throws(()=>validateTask(t));assert.equal(validateTask(t,true).id,t.id);
 for(const patch of [{entry:'http://evil.example/'},{entry:'http://user:pass@127.0.0.1:9001/'},{origins:['http://127.0.0.1:9001/path']},{steps:[{type:'request',method:'POST',url:'https://evil.example/'}]}])assert.throws(()=>validateTask({...t,...patch},true));
});
test('vault encrypts state and config, recovers interrupted runs as unknown',()=>{
 const dir=mkdtempSync(join(tmpdir(),'forum-vault-'));let store=new Store(dir);
 try{const t=task();t.name='TEST_SECRET_CONFIG';store.saveTask(t);store.saveState('a',{cookies:[{value:'TEST_SECRET_COOKIE'}]});const id=store.start(t.id,'daily:test');store.step(id,2);store.close();
 assert.equal(readFileSync(join(dir,'tasks.sqlite')).includes(Buffer.from('TEST_SECRET_COOKIE')),false);
 assert.equal(readFileSync(join(dir,'tasks.sqlite')).includes(Buffer.from('TEST_SECRET_CONFIG')),false);
 store=new Store(dir);assert.equal(store.state('a').cookies[0].value,'TEST_SECRET_COOKIE');assert.equal(store.task(t.id).name,'TEST_SECRET_CONFIG');assert.equal(store.runs()[0].status,'unknown');assert.equal(store.uncertain(t.id),true);
 store.resolve(t.id);assert.equal(store.uncertain(t.id),false);store.clearState('a');assert.equal(store.state('a'),undefined);
 const encrypted=store.seal({a:1});const b=Buffer.from(encrypted,'base64');b[b.length-1]^=1;assert.throws(()=>store.unseal(b.toString('base64')));
 }finally{store.close();rmSync(dir,{recursive:true,force:true});}
});
