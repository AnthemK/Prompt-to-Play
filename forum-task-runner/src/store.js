import { mkdirSync, readdirSync, existsSync, renameSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { createDecipheriv } from 'node:crypto';
import { Store as Vault } from './vault-store.js';

const valid = id => typeof id === 'string' && /^[a-z0-9_-]{1,60}$/.test(id);
// Account IDs are globally unique namespaces. Each owns a separate database and key.
export class Store {
  constructor(dir) {
    this.dir=dir;this.vaults=new Map();this.runOwners=new Map();
    mkdirSync(dir,{recursive:true,mode:0o700});
    this.migrate();
    const root=join(dir,'accounts');mkdirSync(root,{recursive:true,mode:0o700});
    for(const item of readdirSync(root,{withFileTypes:true})) {
      if(item.name==='.complete')continue;
      if(!item.isDirectory() || !valid(item.name))throw Error('Invalid account directory');
      this.vaults.set(item.name,new Vault(join(root,item.name)));
    }
  }
  migrate() {
    const old=join(this.dir,'tasks.sqlite'), marker=join(this.dir,'layout-v2');
    if(existsSync(marker))return;
    if(existsSync(join(this.dir,'accounts','.complete'))){writeFileSync(marker,'account-vaults-v2\n',{mode:0o600});return;}
    if(!existsSync(old)){writeFileSync(marker,'account-vaults-v2\n',{mode:0o600});return;}
    if(existsSync(join(this.dir,'accounts')))throw Error('Migration requires an unambiguous empty destination');
    const stage=join(this.dir,'migration-staging');
    if(existsSync(stage))rmSync(stage,{recursive:true});
    mkdirSync(stage,{mode:0o700});
    const db=new DatabaseSync(old,{readOnly:true});const key=readFileSync(join(this.dir,'vault.key'));
    const unseal=value=>{const b=Buffer.from(value,'base64');const d=createDecipheriv('aes-256-gcm',key,b.subarray(0,12));d.setAuthTag(b.subarray(12,28));return JSON.parse(Buffer.concat([d.update(b.subarray(28)),d.final()]).toString());};
    const opened=new Map();
    try {
      const tasks=db.prepare('SELECT config FROM tasks').all().map(r=>unseal(r.config));
      const states=db.prepare('SELECT account,payload FROM states').all();
      const get=account=>{if(!valid(account))throw Error('Invalid legacy account');if(!opened.has(account))opened.set(account,new Vault(join(stage,account)));return opened.get(account);};
      for(const t of tasks)get(t.account).saveTask(t);
      for(const s of states)get(s.account).saveState(s.account,unseal(s.payload));
      for(const r of db.prepare('SELECT * FROM runs').all()) {
        const t=tasks.find(t=>t.id===r.task);if(!t)throw Error('Orphan legacy run');
        get(t.account).db.prepare('INSERT INTO runs(id,task,period,status,step,started,ended) VALUES (?,?,?,?,?,?,?)').run(r.id,r.task,r.period,r.status,r.step,r.started,r.ended);
      }
      for(const v of opened.values())v.close();opened.clear();
      writeFileSync(join(stage,'.complete'),'migration complete\n',{mode:0o600});
      renameSync(stage,join(this.dir,'accounts'));
      writeFileSync(marker,'account-vaults-v2\n',{mode:0o600});
    }finally{for(const v of opened.values())v.close();db.close();}
    // Preserve old encrypted data for rollback; never use it after the marker exists.
    const backup=join(this.dir,'backups','legacy-v1');mkdirSync(backup,{recursive:true,mode:0o700});
    for(const name of ['tasks.sqlite','tasks.sqlite-wal','tasks.sqlite-shm','vault.key'])if(existsSync(join(this.dir,name)))renameSync(join(this.dir,name),join(backup,name));
  }
  vault(account,create=false) {
    if(!valid(account))throw Error('Invalid account');
    if(!this.vaults.has(account)&&create)this.vaults.set(account,new Vault(join(this.dir,'accounts',account)));
    return this.vaults.get(account);
  }
  tasks(){return [...this.vaults.values()].flatMap(v=>v.tasks()).sort((a,b)=>a.id.localeCompare(b.id));}
  task(id){return this.tasks().find(t=>t.id===id)||null;}
  owner(id){const t=this.task(id);if(!t)throw Error('Unknown task');return this.vault(t.account);}
  saveTask(t){const old=this.task(t.id);if(old&&old.account!==t.account)throw Error('Account reassignment requires explicit migration');const v=this.vault(t.account,true);if(v.tasks().some(x=>x.id!==t.id&&[...x.origins].sort().join()!==[...t.origins].sort().join()))throw Error('Account origin mismatch');v.saveTask(t);}
  state(a){return this.vault(a)?.state(a);}
  saveState(a,s){this.vault(a,true).saveState(a,s);}
  clearState(a){this.vault(a)?.clearState(a);}
  runs(){return [...this.vaults.values()].flatMap(v=>v.runs()).sort((a,b)=>b.started.localeCompare(a.started)).slice(0,100);}
  attempted(t,p){return this.owner(t).attempted(t,p);}
  completed(t,p){return this.owner(t).completed(t,p);}
  uncertain(t){return this.owner(t).uncertain(t);}
  resolve(t){return this.owner(t).resolve(t);}
  start(t,p){const v=this.owner(t),id=v.start(t,p);this.runOwners.set(id,v);return id;}
  step(id,s){this.runOwners.get(id).step(id,s);}
  finish(id,s){this.runOwners.get(id).finish(id,s);this.runOwners.delete(id);}
  close(){for(const v of this.vaults.values())v.close();}
}
