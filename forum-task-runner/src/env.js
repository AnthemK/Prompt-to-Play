import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
export const projectDir=fileURLToPath(new URL('../',import.meta.url));
process.env.PLAYWRIGHT_BROWSERS_PATH ||= resolve(projectDir,'.browsers');
