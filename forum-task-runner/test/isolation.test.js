import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync,readFileSync,existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {Store} from '../src/store.js';
import {Store as Legacy} from '../src/vault-store.js';
import {demoTask} from '../src/demo.js';
test('legacy migration preserves credentials and history in independent vaults and is repeatable',()=>{
 const dir=mkdtempSync(join(tmpdir(),'forum-isolation-'));let s;
 try {
  s=new Legacy(dir);const a=demoTask('http://127.0.0.1:9001');a.account='sjmc';a.id='sjmc-checkin';s.saveTask(a);s.saveState('sjmc',{cookies:[{value:'PRIVATE_A'}]});const id=s.start(a.id,'daily:test');s.finish(id,'already_done');
  const b={...a,id:'other-checkin',account:'other'};s.saveTask(b);s.saveState('other',{cookies:[{value:'PRIVATE_B'}]});s.close();
  s=new Store(dir);assert.equal(s.state('sjmc').cookies[0].value,'PRIVATE_A');assert.equal(s.state('other').cookies[0].value,'PRIVATE_B');assert.equal(s.completed(a.id,'daily:test'),true);
  assert.notDeepEqual(readFileSync(join(dir,'accounts/sjmc/vault.key')),readFileSync(join(dir,'accounts/other/vault.key')));
  assert.equal(existsSync(join(dir,'backups/legacy-v1/tasks.sqlite')),true);
  assert.throws(()=>s.saveTask({...a,account:'other'}));assert.throws(()=>s.saveState('../escape',{}));
  s.clearState('other');assert.equal(s.state('sjmc').cookies[0].value,'PRIVATE_A');s.close();
  s=new Store(dir);assert.equal(s.tasks().length,2);assert.equal(s.runs().length,1);assert.equal(s.state('other'),undefined);
 }finally{s?.close();rmSync(dir,{recursive:true,force:true});}
});
