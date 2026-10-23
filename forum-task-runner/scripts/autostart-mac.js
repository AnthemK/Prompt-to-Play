// Opt-in only: this file is never invoked by the application itself.
import { homedir } from 'node:os';
import { join } from 'node:path';
import { mkdirSync,writeFileSync,existsSync,unlinkSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { projectDir } from '../src/env.js';
if(process.platform!=='darwin')throw Error('此脚本仅适用于 macOS。');
const label='local.forum-task-runner';const target=join(homedir(),'Library','LaunchAgents',label+'.plist');
const domain=`gui/${process.getuid()}`;
const xml=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
if(process.argv.includes('--remove')){
 if(existsSync(target)){spawnSync('launchctl',['bootout',domain,target]);unlinkSync(target);}
 console.log('已移除自动启动配置，任务与登录数据保留。');
}else{
 if(existsSync(target))throw Error('配置已经存在，请先 --remove 再安装。');
 mkdirSync(join(homedir(),'Library','LaunchAgents'),{recursive:true});mkdirSync(join(projectDir,'.data'),{recursive:true,mode:0o700});
 const text=`<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>Label</key><string>${label}</string><key>ProgramArguments</key><array><string>${xml(process.execPath)}</string><string>${xml(join(projectDir,'src/server.js'))}</string></array><key>WorkingDirectory</key><string>${xml(projectDir)}</string><key>RunAtLoad</key><true/><key>KeepAlive</key><dict><key>SuccessfulExit</key><false/></dict><key>ThrottleInterval</key><integer>30</integer><key>StandardOutPath</key><string>${xml(join(projectDir,'.data/service.log'))}</string><key>StandardErrorPath</key><string>${xml(join(projectDir,'.data/service-error.log'))}</string></dict></plist>`;
 writeFileSync(target,text,{mode:0o600,flag:'wx'});
 const r=spawnSync('launchctl',['bootstrap',domain,target],{stdio:'inherit'});
 if(r.status!==0){unlinkSync(target);throw Error('注册失败，已移除本次配置。');}
 console.log('已启用登录后自动启动。请勿再手动启动第二份服务；访问链接见 .data/service.log。');
}
