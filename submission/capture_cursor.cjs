// Fresh UI recordings with a visible pointer. No request interception or fake app state.
const fs=require('node:fs'),path=require('node:path'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),out=path.join(__dirname,'render-v2'),base='http://127.0.0.1:3000';
for(const dir of ['raw','stills'])fs.mkdirSync(path.join(out,dir),{recursive:true});
const key=fs.readFileSync(path.join(root,'backend/.env'),'utf8').match(/^AGENTGATE_OWNER_TOKEN=(.*)$/m)[1].trim().replace(/^['"]|['"]$/g,'');
const paid=JSON.parse(fs.readFileSync(path.join(root,'tmp/submission-mission.json'),'utf8'));
const privateFile=path.join(root,'tmp/cursor-filming.json');
const filming=fs.existsSync(privateFile)?JSON.parse(fs.readFileSync(privateFile,'utf8')):{};
const shotFile=path.join(out,'shots.json'),shots=fs.existsSync(shotFile)?JSON.parse(fs.readFileSync(shotFile,'utf8')):{};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function pointer(){
 addEventListener('DOMContentLoaded',()=>{
  const style=document.createElement('style');style.textContent=`#film-pointer{position:fixed;left:0;top:0;width:32px;height:38px;z-index:2147483647;pointer-events:none;filter:drop-shadow(0 2px 3px #0008);transform:translate(80px,80px)}.film-click{position:fixed;width:62px;height:62px;border:4px solid #e8a126;border-radius:50%;background:#ffc95e35;pointer-events:none;z-index:2147483646;transform:translate(-50%,-50%)}`;document.head.append(style);
  const cursor=document.createElement('div');cursor.id='film-pointer';cursor.innerHTML='<svg width="32" height="38" viewBox="0 0 32 38"><path d="M3 2 3 30 11 23 17 35 23 32 17 21 28 21Z" fill="white" stroke="#142c24" stroke-width="2.5" stroke-linejoin="round"/></svg>';document.body.append(cursor);
  addEventListener('pointermove',e=>{cursor.style.transform=`translate(${e.clientX}px,${e.clientY}px)`},true);
  addEventListener('pointerdown',e=>{const ring=document.createElement('div');ring.className='film-click';ring.style.left=e.clientX+'px';ring.style.top=e.clientY+'px';document.body.append(ring);ring.animate([{opacity:1,scale:.4},{opacity:.8,scale:1},{opacity:0,scale:1.35}],{duration:900,easing:'ease-out'}).finished.then(()=>ring.remove())},true);
 });
}
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});let storageState;
 try{
  const auth=await browser.newContext({viewport:{width:1440,height:720}}),lp=await auth.newPage();await lp.goto(base);await lp.getByLabel('Owner access key').fill(key);await lp.getByRole('button',{name:'Sign in',exact:true}).click();await lp.locator('#selected-budget').waitFor();storageState=await auth.storageState();await auth.close();
  async function record(id,setup,actions){
   if(shots[id]){console.log(id+' retained');return;}
   const ctx=await browser.newContext({viewport:{width:1440,height:720},storageState,recordVideo:{dir:path.join(out,'raw'),size:{width:1440,height:720}},reducedMotion:'reduce'});await ctx.addInitScript(pointer);
   const p=await ctx.newPage(),epoch=Date.now();const errors=[];p.on('pageerror',e=>errors.push(e.message));
   await p.goto(base);await p.locator('#selected-budget').waitFor();await p.evaluate(()=>document.fonts.ready);await setup(p);await sleep(650);
   const start=(Date.now()-epoch)/1000,started=Date.now(),events=[];let previous={x:80,y:80};
   const elapsed=()=> (Date.now()-started)/1000;
   const until=async seconds=>{const ms=seconds*1000-(Date.now()-started);if(ms>0)await sleep(ms)};
   async function reveal(locator){await locator.evaluate(e=>e.scrollIntoView({behavior:'smooth',block:'center'}));await sleep(850)}
   async function move(locator,{zoom=1.38,duration=3.2,label='Focus',revealFirst=true}={}){
    if(revealFirst)await reveal(locator);const box=await locator.boundingBox();if(!box)throw Error('Missing target '+label);
    const point={x:Math.min(1408,Math.max(32,box.x+box.width*.54)),y:Math.min(685,Math.max(35,box.y+Math.min(box.height*.46,140)))};
    events.push({time:elapsed(),duration,zoom,x:point.x,y:point.y,label});
    const from={...previous};for(let i=1;i<=36;i++){const t=i/36,e=t*t*(3-2*t);await p.mouse.move(from.x+(point.x-from.x)*e,from.y+(point.y-from.y)*e);await sleep(10)}previous=point;await sleep(200);return point;
   }
   async function click(locator,opts={}){await move(locator,opts);events.push({time:elapsed(),type:'click',x:previous.x,y:previous.y,label:opts.label||await locator.innerText()});await p.mouse.down();await sleep(65);await p.mouse.up();await sleep(450)}
   await actions(p,{until,reveal,move,click,events,sleep});await sleep(650);const end=(Date.now()-epoch)/1000;
   if(errors.length)throw Error(errors.join('; '));await p.screenshot({path:path.join(out,'stills',id+'.png')});const video=p.video();await ctx.close();
   shots[id]={path:path.relative(root,await video.path()).replaceAll('\\','/'),start,end,viewport:{width:1440,height:720},events};fs.writeFileSync(shotFile,JSON.stringify(shots,null,2));console.log(id+' '+(end-start).toFixed(1)+'s, '+events.filter(e=>e.type==='click').length+' clicks');
  }
  await record('02-mission',async p=>{
   if(!filming.budget){
    const response=p.waitForResponse(r=>r.url().endsWith('/api/gateway/mandates')&&r.request().method()==='POST');
    await p.getByRole('button',{name:'Create a fresh $100 mission budget',exact:true}).click();const created=await(await response).json();filming.budget=created.id;
    if(!filming.budget||filming.budget===paid.mandate_id)throw Error('Fresh filming budget was not created');
    await p.waitForFunction(id=>document.querySelector('#selected-budget')?.value===id,filming.budget);fs.writeFileSync(privateFile,JSON.stringify(filming));
    await p.getByRole('button',{name:'Plan recording mission',exact:true}).click();await p.getByRole('heading',{name:'A complete plan, ready for your review.'}).waitFor({timeout:180000});
   }else{await p.locator('#selected-budget').selectOption(filming.budget);await p.getByRole('heading',{name:'A complete plan, ready for your review.'}).waitFor()}
   await p.evaluate(()=>window.scrollTo(0,0));
  },async(p,h)=>{
   await h.until(1);await h.move(p.locator('.budget-strip'),{zoom:1.25,duration:3,label:'Shared $100 budget',revealFirst:false});
   await h.until(5);await h.move(p.locator('.agent-handoff'),{zoom:1.4,duration:4,label:'Iris hands her cart and remainder to Nova'});
   await h.until(11);await h.move(p.locator('.mission-carts'),{zoom:1.3,duration:4.5,label:'Actual model carts'});await h.until(18.4);
  });
  // Inspect the preserved actual replan from the completed payment mission.
  await record('03-replan',async p=>{await p.locator('#selected-budget').selectOption(paid.mandate_id);await p.locator('.decision-rejected').waitFor();},async(p,h)=>{
   const rows=p.locator('.mission-decision'),rejected=p.locator('.decision-rejected').first();
   await h.move(rows.first(),{zoom:1.3,duration:2.1,label:'Iris proposes the $80 microphone'});await h.until(2.8);
   await h.move(rejected.locator('.decision-content'),{zoom:1.45,duration:4,label:'$45 rejected against $20 remaining'});await h.until(7.8);
   await h.click(rejected.locator('summary'),{zoom:1.35,duration:3.8,label:'Inspect the actual policy checks'});await h.until(12.4);
   await h.move(rows.last().locator('.decision-content'),{zoom:1.42,duration:6.5,label:'The model replans to a $20 cable kit'});await h.until(23);
  });
  await record('04-approval',async p=>{await p.locator('#selected-budget').selectOption(filming.budget);await p.getByRole('heading',{name:'A complete plan, ready for your review.'}).waitFor();await p.locator('.mission-result').evaluate(e=>e.scrollIntoView({block:'start'}));},async(p,h)=>{
   await h.move(p.locator('.mission-totals'),{zoom:1.38,duration:3.2,label:'Planning has reserved zero',revealFirst:false});await h.until(4);
   await h.click(p.getByRole('button',{name:/Approve exact mission carts/}),{zoom:1.45,duration:4.5,label:'Owner approves both exact carts'});
   await p.getByText('Exact mission carts approved together. Their combined amount is now reserved.',{exact:true}).waitFor();
   await h.until(9);await h.move(p.locator('.mission-totals'),{zoom:1.35,duration:4.3,label:'$100 now reserved atomically'});
   await h.until(14);await h.click(p.locator('.mission-binding').first().locator('summary'),{zoom:1.4,duration:4.5,label:'Exact-cart fingerprint'});await h.until(20);
  });
  await record('05-paypal-live',async p=>{await p.locator('#selected-budget').selectOption(paid.mandate_id);await p.getByRole('heading',{name:'Mission paid. Receipts recorded.'}).waitFor();},async(p,h)=>{
   await h.move(p.locator('.mission-totals'),{zoom:1.3,duration:3,label:'Completed $100 mission'});await h.until(4);
   await h.click(p.getByRole('button',{name:'Payment evidence',exact:true}),{zoom:1.5,duration:2.2,label:'Open PayPal evidence',revealFirst:false});
   const cards=paid.paid.map(c=>p.locator('.evidence-receipt').filter({hasText:c.receipt.id}));
   for(let i=0;i<cards.length;i++){
    if(i===1)await h.until(15);
    const card=cards[i];const checked=p.waitForResponse(r=>r.url().includes('/proposals/')&&r.url().endsWith('/verify')&&r.request().method()==='POST',{timeout:65000});
    await h.click(card.getByRole('button',{name:'Verify with PayPal',exact:true}),{zoom:1.35,duration:3.8,label:'Read original PayPal order'});
    if(!(await checked).ok())throw Error('Provider verification failed');await card.getByText('Provider response matches the saved receipt',{exact:true}).waitFor({timeout:65000});await h.move(card.locator('.evidence-verified'),{zoom:1.4,duration:3.7,label:'Provider receipt matches'});await sleep(1700);
   }await h.until(24);
  });
  await record('06-recovery',async p=>{await p.getByRole('button',{name:'Payment evidence',exact:true}).click();},async(p,h)=>{
   const card=p.locator('.evidence-receipt').filter({hasText:paid.paid[0].receipt.id});
   await h.click(card.getByRole('button',{name:'Replay saved receipt',exact:true}),{zoom:1.38,duration:2.1,label:'Replay the same receipt'});
   const replayNotice=p.getByText('Original receipt returned. No new capture was initiated.',{exact:true});await replayNotice.waitFor();await h.move(replayNotice,{zoom:1.4,duration:2.7,label:'Original receipt returned without a new capture'});await h.until(6);
   await h.click(p.getByRole('button',{name:'Failure lab',exact:true}),{zoom:1.45,duration:2.2,label:'Open isolated failure lab',revealFirst:false});
   await h.click(p.getByRole('button',{name:'Run suite',exact:true}),{zoom:1.4,duration:3,label:'Run simulated failure cases'});await p.locator('.lab-score').waitFor();
   await h.until(12);await h.move(p.locator('.result-row').nth(2),{zoom:1.18,duration:5,label:'Ten isolated controls'});await h.until(21);
  });
  await record('07-evaluation',async p=>{await p.getByRole('button',{name:'Live benchmark',exact:true}).click();await p.getByText('6 / 6',{exact:true}).waitFor();},async(p,h)=>{
   await h.move(p.locator('.mission-evaluation'),{zoom:1.18,duration:4.8,label:'Two-model evaluation'});await h.until(6);
   await h.move(p.locator('.mission-eval-table').first(),{zoom:1.35,duration:4.5,label:'Task matching and accepted policy violations'});await h.until(12);
   await h.click(p.getByText('Inspect each mission outcome',{exact:true}),{zoom:1.4,duration:3.5,label:'Inspect the misses too'});
   await h.until(16);await h.move(p.locator('.mission-evaluation details tbody tr').filter({hasText:'Missed'}).first(),{zoom:1.2,duration:3.5,label:'All mission outcomes, including the missed task'});await h.until(22);
  });
  // Release this filming run's extra reservations, without creating any orders.
  if(!filming.released){const ctx=await browser.newContext({storageState}),p=await ctx.newPage();await p.goto(base);await p.locator('#selected-budget').waitFor();await p.locator('#selected-budget').selectOption(filming.budget);
   if(filming.budget===paid.mandate_id)throw Error('Refusing to release the captured submission mission');
   const state=await(await p.request.get(base+'/api/gateway/state')).json();
   for(const cart of state.proposals.filter(c=>c.mandate_id===filming.budget&&c.state==='approved')){
    const r=await p.request.post(base+`/api/gateway/proposals/${cart.id}/cancel`,{headers:{Origin:base},data:{cart_hash:cart.cart_hash}});if(!r.ok())throw Error('Could not release filming reservation');
   }
   filming.released=true;fs.writeFileSync(privateFile,JSON.stringify(filming));await ctx.close();}
 }finally{await browser.close()}
})().catch(e=>{console.error(String(e).replaceAll(key,'[redacted]'));process.exitCode=1});
