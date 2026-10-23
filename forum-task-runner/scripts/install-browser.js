import '../src/env.js';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const cli = fileURLToPath(new URL('../node_modules/playwright/cli.js', import.meta.url));
const result = spawnSync(process.execPath, [cli, 'install', 'chromium'], { stdio: 'inherit', env: process.env });
if (result.error) console.error('浏览器安装失败，请检查网络与依赖。');
process.exit(result.status ?? 1);
