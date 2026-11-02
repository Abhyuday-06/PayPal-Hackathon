// Actual app recordings. No request interception or fabricated application state.
const fs=require('node:fs'), path=require('node:path');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'), out=path.join(__dirname,'render');
fs.mkdirSync(path.join(out,'raw'),{recursive:true});fs.mkdirSync(path.join(out,'stills'),{recursive:true});
const key=fs.readFileSync(path.join(root,'backend/.env'),'utf8').match(/^AGENTGATE_OWNER_TOKEN=(.*)$/m)[1].trim().replace(/^['"]|['"]$/g,'');
const original=JSON.parse(fs.readFileSync(path.join(root,'tmp/submission-mission.json'),'utf8'));
const base='http://127.0.0.1:3000';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const shots=fs.existsSync(path.join(out,'shots.json'))?JSON.parse(fs.readFileSync(path.join(out,'shots.json'),'utf8')):{};
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try{
  const login=await browser.newContext({viewport:{width:1600,height:1000}});const lp=await login.newPage();await lp.goto(base);await lp.getByLabel('Owner access key').fill(key);await lp.getByRole('button',{name:'Sign in',exact:true}).click();await lp.getByRole('heading',{name:'One mission. Two agents. A shared budget.'}).waitFor();const storageState=await login.storageState();await login.close();
  async function record(id,setup,actions){
   if(shots[id]){console.log(id+' retained');return;}
   const ctx=await browser.newContext({viewport:{width:1600,height:1000},storageState,recordVideo:{dir:path.join(out,'raw'),size:{width:1600,height:1000}},reducedMotion:'reduce'});
   const p=await ctx.newPage();const epoch=Date.now();p.on('pageerror',e=>{throw Error(e.message.replaceAll(key,'[redacted]'))});
   await p.goto(base);await p.getByRole('heading',{name:'One mission. Two agents. A shared budget.'}).waitFor();await setup(p);await p.evaluate(()=>window.scrollTo(0,0));await sleep(500);
   const start=(Date.now()-epoch)/1000;await actions(p);await sleep(1000);const end=(Date.now()-epoch)/1000;
   await p.screenshot({path:path.join(out,'stills',id+'.png')});const video=p.video();await ctx.close();shots[id]={path:path.relative(root,await video.path()).replaceAll('\\','/'),start,end};fs.writeFileSync(path.join(out,'shots.json'),JSON.stringify(shots,null,2));console.log(id,Math.round(end-start)+'s');
  }
  // A fresh, actually generated plan supplies the planning views. The buyer-approved
  // mission supplies payment capture footage. Both use the same $80 + $20 exact carts.
  let planningBudget;
  await record('02-mission',async p=>{
   await p.getByRole('button',{name:'Create a fresh $100 mission budget',exact:true}).click();await p.getByText('Fresh $100 policy budget created. No funds are reserved until you approve exact carts.',{exact:true}).waitFor();
   await p.getByRole('button',{name:'Plan recording mission',exact:true}).click();await p.getByRole('heading',{name:'A complete plan, ready for your review.'}).waitFor({timeout:120000});planningBudget=await p.locator('#selected-budget').inputValue();
  },async p=>{await sleep(3000);await p.locator('.mission-result').scrollIntoViewIfNeeded();await sleep(4000);await p.evaluate(()=>window.scrollTo({top:0,behavior:'smooth'}));await sleep(4000);});
  await record('03-replan',p=>p.locator('#selected-budget').selectOption(planningBudget),async p=>{
   await p.locator('.mission-decisions').scrollIntoViewIfNeeded();await sleep(4000);const rejected=p.locator('.decision-rejected').first();if(await rejected.count()){await rejected.scrollIntoViewIfNeeded();await rejected.locator('summary').click();await sleep(5500);}await p.locator('.mission-decision').last().scrollIntoViewIfNeeded();await sleep(5500);
  });
  await record('04-approval',p=>p.locator('#selected-budget').selectOption(planningBudget),async p=>{
   await p.getByRole('button',{name:/Approve exact mission carts/}).click();await p.getByText('Exact mission carts approved together. Their combined amount is now reserved.',{exact:true}).waitFor();await p.evaluate(()=>window.scrollTo(0,0));await sleep(4500);await p.locator('.mission-binding').first().locator('summary').click();await sleep(5000);await p.evaluate(()=>window.scrollTo(0,0));await sleep(3000);
  });
  await record('05-paypal-live',p=>p.locator('#selected-budget').selectOption(original.mandate_id),async p=>{
   for(const cart of await p.locator('.mission-cart').all()){
    const confirm=cart.getByRole('button',{name:'Confirm PayPal capture',exact:true});
    if(await confirm.count()){await confirm.click();await cart.getByText('PayPal sandbox confirmed',{exact:true}).waitFor({timeout:65000});await sleep(1600);}
   }
   await p.getByRole('heading',{name:'Mission paid. Receipts recorded.'}).waitFor();await p.evaluate(()=>window.scrollTo(0,0));await sleep(3500);
   await p.getByRole('button',{name:'Payment evidence',exact:true}).click();
   const state=await(await p.request.get(base+'/api/gateway/state')).json();const paid=state.proposals.filter(c=>c.mandate_id===original.mandate_id&&c.state==='captured');if(paid.length!==2)throw Error('Both real sandbox captures were not completed');
   original.paid=paid;fs.writeFileSync(path.join(root,'tmp/submission-mission.json'),JSON.stringify(original));
   for(const c of paid){const card=p.locator('.evidence-receipt').filter({hasText:c.receipt.id});await card.getByRole('button',{name:'Verify with PayPal',exact:true}).click();await card.getByText('Provider response matches the saved receipt',{exact:true}).waitFor({timeout:65000});await sleep(2500);}
  });
  await record('06-recovery',async p=>{await p.getByRole('button',{name:'Payment evidence',exact:true}).click()},async p=>{
   const card=p.locator('.evidence-receipt').filter({hasText:original.paid[0].receipt.id});await card.getByRole('button',{name:'Replay saved receipt',exact:true}).click();await p.getByText('Original receipt returned. No new capture was initiated.',{exact:true}).waitFor();await sleep(3500);
   await p.getByRole('button',{name:'Failure lab',exact:true}).click();await p.getByRole('button',{name:'Run suite',exact:true}).click();await p.locator('.lab-score').waitFor();await sleep(3500);await p.locator('.results-table').scrollIntoViewIfNeeded();await sleep(5500);
  });
  await record('07-evaluation',async p=>{await p.getByRole('button',{name:'Live benchmark',exact:true}).click();await p.getByText('6 / 6',{exact:true}).waitFor()},async p=>{
   await p.locator('.mission-evaluation').scrollIntoViewIfNeeded();await sleep(5000);await p.getByText('Inspect each mission outcome',{exact:true}).click();await p.locator('.mission-evaluation details').scrollIntoViewIfNeeded();await sleep(5500);await p.locator('.mission-evaluation').scrollIntoViewIfNeeded();await sleep(3500);
  });
  await record('08-close',async p=>{await p.getByRole('button',{name:'Recording mission',exact:true}).click();await p.locator('#selected-budget').selectOption(original.mandate_id)},async p=>{await p.evaluate(()=>window.scrollTo(0,0));await sleep(6000)});
  // Release only the extra filming plan's reservations; the captured mission is preserved.
  const ctx=await browser.newContext({storageState});const page=await ctx.newPage();await page.goto(base);await page.getByRole('heading',{name:'One mission. Two agents. A shared budget.'}).waitFor();if(planningBudget) await page.locator('#selected-budget').selectOption(planningBudget);
  for(const b of planningBudget ? await page.getByRole('button',{name:'Release this reservation',exact:true}).all() : []){await b.click();await sleep(500);}await ctx.close();
 }finally{await browser.close()}
})().catch(e=>{console.error(String(e).replaceAll(key,'[redacted]'));process.exitCode=1});
