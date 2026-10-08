// Export the validated viewer's canonical SVG for GitHub's README renderer.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { ChromeVisualBrowser, findChrome } from '../.agents/skills/archify/bin/visual-check.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const browser = new ChromeVisualBrowser(findChrome());
try {
  const session = await browser.sessionPromise;
  const send = (method, params = {}) => browser.cdp.send(method, params, session);
  await browser.cdp.send('Browser.setDownloadBehavior', { behavior: 'deny' });
  const loaded = browser.cdp.waitFor('Page.loadEventFired', session);
  await send('Page.navigate', { url: pathToFileURL(path.join(root, 'docs/architecture/prd-context.html')).href });
  await loaded;
  const result = await send('Runtime.evaluate', { awaitPromise: true, returnByValue: true,
    expression: `(async () => {
      await document.fonts.ready;
      await Archify.readerLayout.whenStable();
      const original = URL.createObjectURL;
      let blob;
      URL.createObjectURL = function(value) {
        if (value.type.startsWith('image/svg+xml')) blob = value;
        return original.call(URL, value);
      };
      try { await Archify.exportMenu.run('svg-light'); }
      finally { URL.createObjectURL = original; }
      if (!blob) throw new Error('No SVG export produced');
      return await blob.text();
    })()` });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  fs.writeFileSync(path.join(root, 'docs/architecture/prd-context.svg'),
    result.result.value.replace(/[ \t]+$/gm, ''));
  console.log('Exported docs/architecture/prd-context.svg');
} finally {
  await browser.close();
}
