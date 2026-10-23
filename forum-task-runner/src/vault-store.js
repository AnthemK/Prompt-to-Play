import { DatabaseSync } from 'node:sqlite';
import { mkdirSync, readFileSync, writeFileSync, existsSync, chmodSync } from 'node:fs';
import { join } from 'node:path';
import { randomBytes, createCipheriv, createDecipheriv, randomUUID } from 'node:crypto';
export class Store {
  constructor(dir) {
    mkdirSync(dir,{recursive:true,mode:0o700}); chmodSync(dir,0o700);
    const keyFile=join(dir,'vault.key');
    if (!existsSync(keyFile)) writeFileSync(keyFile,randomBytes(32),{mode:0o600,flag:'wx'});
    this.key=readFileSync(keyFile); if(this.key.length!==32) throw Error('Invalid vault key');
    this.db=new DatabaseSync(join(dir,'tasks.sqlite'));
    chmodSync(join(dir,'tasks.sqlite'),0o600);
    this.db.exec(`PRAGMA journal_mode=WAL; CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, config TEXT NOT NULL); CREATE TABLE IF NOT EXISTS states(account TEXT PRIMARY KEY, payload TEXT NOT NULL); CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, task TEXT NOT NULL, period TEXT NOT NULL, status TEXT NOT NULL, step INTEGER DEFAULT -1, started TEXT NOT NULL, ended TEXT); CREATE INDEX IF NOT EXISTS runs_period ON runs(task,period);`);
    this.db.prepare("UPDATE runs SET status='unknown', ended=? WHERE status='running'").run(new Date().toISOString());
  }
  seal(data) { const iv=randomBytes(12);const c=createCipheriv('aes-256-gcm',this.key,iv);const body=Buffer.concat([c.update(JSON.stringify(data),'utf8'),c.final()]);return Buffer.concat([iv,c.getAuthTag(),body]).toString('base64'); }
  unseal(value) { const b=Buffer.from(value,'base64');const d=createDecipheriv('aes-256-gcm',this.key,b.subarray(0,12));d.setAuthTag(b.subarray(12,28));return JSON.parse(Buffer.concat([d.update(b.subarray(28)),d.final()]).toString()); }
  tasks() { return this.db.prepare('SELECT config FROM tasks ORDER BY id').all().map(x=>this.unseal(x.config)); }
  task(id) { const r=this.db.prepare('SELECT config FROM tasks WHERE id=?').get(id);return r?this.unseal(r.config):null; }
  saveTask(t) {this.db.prepare('INSERT INTO tasks VALUES (?,?) ON CONFLICT(id) DO UPDATE SET config=excluded.config').run(t.id,this.seal(t));}
  state(account) {const r=this.db.prepare('SELECT payload FROM states WHERE account=?').get(account);return r?this.unseal(r.payload):undefined;}
  saveState(account,state) {this.db.prepare('INSERT INTO states VALUES (?,?) ON CONFLICT(account) DO UPDATE SET payload=excluded.payload').run(account,this.seal(state));}
  clearState(account) {this.db.prepare('DELETE FROM states WHERE account=?').run(account);}
  runs() {return this.db.prepare('SELECT * FROM runs ORDER BY started DESC LIMIT 100').all();}
  attempted(task,period) {return !!this.db.prepare('SELECT 1 FROM runs WHERE task=? AND period=? LIMIT 1').get(task,period);}
  completed(task,period) {return !!this.db.prepare("SELECT 1 FROM runs WHERE task=? AND period=? AND status IN ('success','already_done') LIMIT 1").get(task,period);}
  uncertain(task) {return !!this.db.prepare("SELECT 1 FROM runs WHERE task=? AND status='unknown' LIMIT 1").get(task);}
  resolve(task) {this.db.prepare("UPDATE runs SET status='reviewed' WHERE task=? AND status='unknown'").run(task);}
  start(task,period) {const id=randomUUID();this.db.prepare('INSERT INTO runs(id,task,period,status,started) VALUES (?,?,?,?,?)').run(id,task,period,'running',new Date().toISOString());return id;}
  step(id,step) {this.db.prepare('UPDATE runs SET step=? WHERE id=?').run(step,id);}
  finish(id,status) {this.db.prepare('UPDATE runs SET status=?,ended=? WHERE id=?').run(status,new Date().toISOString(),id);}
  close() {this.db.close();}
}
