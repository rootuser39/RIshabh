/* Optional browser verification. No dependency is required by the website itself. */
const fs = require('fs');
const path = require('path');
const assert = require('node:assert/strict');
const {spawn} = require('child_process');
const ROOT = path.resolve(__dirname,'..');
const resolvePaths = process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES ? [process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES] : [ROOT];
const {chromium} = require(require.resolve('playwright',{paths:resolvePaths}));
const SHOTS = path.join(ROOT,'test-results');
const content = name => JSON.parse(fs.readFileSync(path.join(ROOT,'content',name+'.json'),'utf8'));
const systems = content('systems');
const records = [...content('experiments'),...content('field-logs'),...content('failures')];
const runtimeSystems = content('map').layers.find(layer=>layer.id==='runtime').systems.filter(id=>systems.some(system=>system.id===id));
let browser;
let server;

(async () => {
  fs.mkdirSync(SHOTS,{recursive:true});
  server=spawn(process.env.LAB_PYTHON || 'python',['-m','http.server','8087','--bind','127.0.0.1'],{cwd:ROOT,stdio:'ignore'});
  let ready=false;
  for(let i=0;i<60;i++) {
    try { const r=await fetch('http://127.0.0.1:8087/',{method:'HEAD'});if(r.ok) {ready=true;break;} } catch {}
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  assert(ready,'Local verification server started');
  browser=await chromium.launch({headless:true,executablePath:process.env.LAB_CHROMIUM_PATH || undefined,args:['--no-sandbox','--disable-dev-shm-usage']});
  const context=await browser.newContext({reducedMotion:'reduce'});
  const page=await context.newPage();
  const errors=[];
  const requests=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',msg=>{if(msg.type()==='error')errors.push(msg.text());});
  page.on('request',r=>requests.push(r.url()));
  const layouts=[];
  for(const width of [360,390,430,768,1280]) {
    await page.setViewportSize({width,height:900});
    await page.goto('http://127.0.0.1:8087/');
    await page.waitForFunction(()=>document.documentElement.classList.contains('enhanced'));
    if(width===360) {
      await page.keyboard.press('Tab');
      assert.equal(await page.locator(':focus').getAttribute('class'),'skip-link','Skip link is first in keyboard order');
      assert.equal(await page.locator(':focus').evaluate(e=>getComputedStyle(e).clipPath),'none','Skip link is visible when focused');
      assert.equal(await page.locator(':focus').evaluate(e=>getComputedStyle(e).outlineWidth),'2px','Visible keyboard focus');
      await page.keyboard.press('Enter');
      assert.equal(await page.locator(':focus').getAttribute('id'),'main','Skip link transfers focus to main');
    }
    await page.evaluate(()=>Promise.all([...document.images].filter(img=>img.loading!=='lazy').map(img=>img.decode())));
    const report=await page.evaluate(()=>({
      width:innerWidth,scroll:document.documentElement.scrollWidth,
      headings:document.querySelectorAll('h1').length,
      loadedHero:document.querySelector('.hero-art img').naturalWidth,
      hero:document.querySelector('.hero-art img').currentSrc,
      pet:document.querySelector('.pet').getBoundingClientRect().width,
      externalImages:[...document.images].filter(img=>!img.src.startsWith(location.origin)).length,
    }));
    assert.equal(report.scroll,width,'No horizontal page overflow');
    assert.equal(report.headings,1,'Exactly one central h1');
    assert(report.loadedHero>0,'Hero loaded');
    assert.equal(report.externalImages,0,'Only local images');
    assert(report.hero.includes('/still/'),'Reduced-motion source selected');
    if(width<=640)assert(report.hero.endsWith('observatory-mobile.svg'),'Portrait mobile hero');
    layouts.push(report);
    if(width===390 || width===1280)await page.screenshot({path:path.join(SHOTS,`lab-${width}.png`),fullPage:true});
  }
  await page.setViewportSize({width:390,height:900});
  await page.goto('http://127.0.0.1:8087/');
  await page.locator('#system-argus summary').click();
  assert(await page.locator('#system-argus').evaluate(e=>e.open),'System opens by touch');
  await page.locator('#system-argus').screenshot({path:path.join(SHOTS,'argus-mobile.png')});
  await page.locator('#signal').screenshot({path:path.join(SHOTS,'signal-mobile.png')});
  assert(await page.locator('#system-argus').innerText().then(text=>text.includes('non-empty output')),'Verification boundary visible');
  await page.locator('[data-filter-group="evidence"][data-filter="argus"]').click();
  assert.equal(await page.locator('#evidence .record:visible').count(),records.filter(record=>record.system==='argus').length,'Filter preserves related records');
  await page.locator('[data-filter-group="evidence"][data-filter="all"]').click();
  assert.equal(await page.locator('#evidence .record:visible').count(),records.length,'All authentic records return');
  await page.locator('[data-layer="runtime"]').click();
  assert.equal(await page.locator('.system.context-active').count(),runtimeSystems.length,'Layer maps to documented scope');
  await page.locator('[data-filter-group="tools"][data-filter="COMPUTE"]').click();
  assert.equal(await page.locator('.tool:visible').count(),content('tools').filter(tool=>tool.category==='COMPUTE').length,'Instrument roles filter');
  await page.locator('#E-001 summary').click();
  await page.waitForFunction(()=>document.querySelector('.pet').dataset.state==='working');
  assert.equal(await page.locator('.pet').getAttribute('data-state'),'working','Dragon reacts to inspection');
  await page.screenshot({path:path.join(SHOTS,'records-open-mobile.png'),fullPage:true});

  // Five keyboard activations unlock the same channel as taps.
  const omega=page.locator('.omega-trigger');
  await omega.focus();
  for(let i=0;i<5;i++)await page.keyboard.press('Enter');
  assert(await page.locator('#abyss-terminal').evaluate(e=>e.open),'Omega terminal unlocked');
  assert.equal(await page.locator(':focus').getAttribute('id'),'terminal-command','Command receives focus');
  for(const value of ['help','systems','experiments','failures','signal','dragon','whoami','<img src=x onerror=alert(1)>']) {
    await page.locator('#terminal-command').fill(value);
    await page.locator('#terminal-command').press('Enter');
  }
  assert.equal(await page.locator('#terminal-output img').count(),0,'User input stays inert text');
  assert((await page.locator('#terminal-output').innerText()).includes('Unknown command'),'Command whitelist');
  await page.screenshot({path:path.join(SHOTS,'terminal-mobile.png')});
  await page.keyboard.press('Escape');
  assert.equal(await page.locator(':focus').getAttribute('class'),'omega-trigger enhancement','Dialog restores keyboard focus');

  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.locator('#motion-toggle').click();
  assert(await page.locator('html').evaluate(e=>e.classList.contains('motion-off')),'Manual motion pause');
  assert(await page.locator('.hero-art img').evaluate(img=>img.currentSrc.includes('/still/')),'Manual pause selects still artwork');
  const hero=page.locator('.hero-art img');
  const still1=await hero.screenshot();
  await page.waitForTimeout(450);
  const still2=await hero.screenshot();
  assert(still1.equals(still2),'Still image stays still');
  assert.equal(await page.evaluate(()=>document.getAnimations().filter(a=>a.playState==='running').length),0,'Inline motion is stopped too');
  await page.locator('#motion-toggle').click();
  assert(await hero.evaluate(img=>!img.currentSrc.includes('/still/')),'Normal artwork restored');
  const animated1=await hero.screenshot();
  await page.waitForTimeout(450);
  const animated2=await hero.screenshot();
  assert(!animated1.equals(animated2),'Normal embedded artwork animates under the content security policy');

  await page.locator('#signal').scrollIntoViewIfNeeded();
  await page.clock.install();
  await page.getByRole('button',{name:'Observe',exact:true}).click();
  await page.clock.fastForward(91000);
  assert.equal(await page.locator('.pet').getAttribute('data-state'),'sleeping','Companion sleeps after inactivity');
  await page.getByRole('button',{name:'Observe',exact:true}).click();
  assert.equal(await page.locator('.pet').getAttribute('data-state'),'observing','Touch wakes the companion');

  const noJS=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:900},reducedMotion:'reduce'});
  const plain=await noJS.newPage();
  await plain.goto('http://127.0.0.1:8087/');
  assert.equal(await plain.locator('#evidence .record').count(),records.length,'Evidence is rendered without JavaScript');
  await plain.locator('#system-fabric summary').click();
  assert(await plain.locator('#system-fabric').evaluate(e=>e.open),'Native disclosure works without JavaScript');
  assert.equal(await plain.locator('.filters:visible').count(),0,'Unavailable enhancements are hidden');
  assert.equal(await plain.evaluate(()=>document.documentElement.scrollWidth),390,'No-JS mobile layout fits');
  await noJS.close();
  assert.equal(errors.length,0,JSON.stringify(errors));
  assert(requests.every(url=>url.startsWith('http://127.0.0.1:8087/')),'No external runtime request');
  console.log(JSON.stringify({layouts,errors,interactionChecks:'passed',noJavaScript:'passed',motion:'passed'},null,2));
})().then(async()=>{await browser?.close();server?.kill();}).catch(async error=>{console.error(error);await browser?.close();server?.kill();process.exitCode=1;});
