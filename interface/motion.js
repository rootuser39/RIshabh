/* One foreground task; otherwise the observatory rests. No service is executed. */
(() => {
  'use strict';
  const content=JSON.parse(document.getElementById('lab-content').textContent);
  const root=document.documentElement;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const pet=document.querySelector('.pet');
  const resident=document.querySelector('.pet-stage');
  const petLabel=document.getElementById('pet-state');
  const ns='http://www.w3.org/2000/svg';
  let stopped=reduced.matches,task=null,reactionTimer,idleTimer,scrollTimer,coreTimer,priorPerch='home',terminalActive=false;
  const visible=new Set();
  const controllers=new Map();
  const all=(s,p=document)=>Array.from(p.querySelectorAll(s));
  const svg=(tag,attrs={})=>{const node=document.createElementNS(ns,tag);for(const [key,value] of Object.entries(attrs))node.setAttribute(key,String(value));return node;};
  const canMove=()=>!stopped&&!reduced.matches&&!document.hidden&&typeof Element.prototype.animate==='function';
  const inView=node=>{const r=node.getBoundingClientRect();return !!node.getClientRects().length&&r.bottom>0&&r.top<innerHeight;};
  function status(owner,value){const node=owner.querySelector('.trace-status');if(node)node.textContent=value;}
  function state(value,duration=0){
    if(document.hidden&&value!=='sleeping')return;
    clearTimeout(reactionTimer);pet.dataset.state=value;petLabel.textContent=value.toUpperCase();
    if(duration)reactionTimer=setTimeout(()=>{if(!document.hidden)state('idle');},duration);
  }
  function resetIdle(){
    clearTimeout(idleTimer);
    if(pet.dataset.state==='sleeping'&&!document.hidden)state('idle');
    if(!document.hidden)idleTimer=setTimeout(()=>state('sleeping'),90000);
  }
  function settle(){
    if(!task)return;
    const previous=task;task=null;previous.cancelled=true;
    for(const {id,resolve} of previous.waits){clearTimeout(id);resolve(false);}
    for(const animation of previous.animations)animation.cancel();
    for(const node of previous.nodes)node.remove();
    previous.owner.classList.remove('trace-running','card-active','core-notice');
    previous.cleanup?.();
    root.classList.remove('ambient-yield');
  }
  function begin(owner,cleanup){
    settle();
    if(!canMove()||!inView(owner))return null;
    task={owner,cleanup,cancelled:false,waits:[],animations:[],nodes:[]};
    owner.classList.add('trace-running');root.classList.add('ambient-yield');
    return task;
  }
  const valid=t=>!!t&&!t.cancelled&&task===t&&canMove();
  function wait(t,ms){
    if(!valid(t))return Promise.resolve(false);
    return new Promise(resolve=>{const item={resolve,id:setTimeout(()=>{t.waits=t.waits.filter(v=>v!==item);resolve(valid(t));},ms)};t.waits.push(item);});
  }
  async function animate(t,node,frames,duration){
    if(!valid(t))return false;
    const animation=node.animate(frames,{duration,easing:'linear',fill:'forwards'});
    t.animations.push(animation);
    try{await animation.finished;}catch{return false;}
    return valid(t);
  }
  function finish(t){if(valid(t))settle();}
  async function packet(t,plane,points,duration=900){
    if(!valid(t)||points.length<2)return false;
    const fabricScale=!!plane.closest('.fabric-board');
    const node=svg('rect',{class:'packet',x:fabricScale?-.3:-2,y:fabricScale?-.6:-2,width:fabricScale?.6:4,height:fabricScale?1.2:4,rx:fabricScale?.15:1});plane.append(node);t.nodes.push(node);
    const frames=points.map((p,i)=>({transform:'translate('+p[0]+'px,'+p[1]+'px)',offset:i/(points.length-1)}));
    const ok=await animate(t,node,frames,duration);node.remove();return ok;
  }
  function relocate(name,pose='observing',restore=false){
    if(terminalActive&&name!=='terminal')return;
    const zone=document.querySelector('[data-perch="'+name+'"]')||document.querySelector('[data-perch="home"]');
    if(!zone||(!restore&&!inView(zone))||resident.contains(document.activeElement))return;
    const old=resident.closest('[data-perch]');
    if(old!==zone){old?.setAttribute('aria-hidden','true');zone.removeAttribute('aria-hidden');zone.append(resident);}
    pet.classList.toggle('motion-visible',inView(pet));
    if(canMove()&&inView(zone)&&name!=='home'&&!restore){
      state('walking');
      const a=resident.animate([{transform:'translateX(-6px)'},{transform:'translateX(-3px)'},{transform:'translateX(0)'}],{duration:480,easing:'linear'});
      a.finished.then(()=>{if(pet.dataset.state==='walking')state(pose,2500);}).catch(()=>{});
    }else state(pose,2500);
  }
  function react(pose='observing',duration=2500){state(pose,duration);resetIdle();}
  function staticArchitecture(owner){
    const empty=owner.dataset.system==='argus'&&owner.dataset.output==='empty';
    all('[data-step]',owner).forEach(node=>{
      const skip=empty&&node.hasAttribute('data-memory');
      node.classList.remove('active');node.classList.toggle('skipped',skip);node.classList.toggle('visited',!skip);
      node.querySelector('.step-state').textContent=skip?'SKIPPED':node.hasAttribute('data-memory')?'CONDITIONAL WRITE':'PATH';
    });
    status(owner,owner.dataset.system==='argus'?(empty?'Empty text → memory skipped → trace returned with verified: false.':'Non-empty text → conditional JSONL write → returned trace. Presence does not establish correctness.'):'Conceptual path selected; implementation boundary stays in the system record.');
    drawArchitecture(owner);
  }
  function drawArchitecture(owner){
    const board=owner.querySelector('.trace-board'),plane=board.querySelector('svg'),r=board.getBoundingClientRect();
    plane.replaceChildren();plane.setAttribute('viewBox','0 0 '+Math.max(1,r.width)+' '+Math.max(1,r.height));
    const nodes=all('[data-step]',owner).filter(v=>!v.classList.contains('skipped'));
    owner._points=nodes.map(v=>({node:v,p:[12,v.offsetTop+v.offsetHeight/2]}));
    owner._points.forEach(({p,node},i)=>{
      plane.append(svg('path',{d:'M 12 '+p[1]+' H 27',class:'selected'}));
      if(i){const prev=owner._points[i-1],bypass=node.dataset.step-prev.node.dataset.step>1;
        plane.append(svg('path',{d:bypass?'M 12 '+prev.p[1]+' H 3 V '+p[1]+' H 12':'M 12 '+prev.p[1]+' V '+p[1],class:'selected'+(bypass?' bypass':'')}));
      }
    });
  }
  async function playArchitecture(owner){
    staticArchitecture(owner);relocate(owner.id,'working');
    const t=begin(owner,()=>all('.active',owner).forEach(v=>v.classList.remove('active')));
    if(!t)return;
    const points=owner._points;
    all('[data-step]',owner).forEach(v=>{v.classList.remove('visited');if(!v.classList.contains('skipped'))v.querySelector('.step-state').textContent='READY';});
    for(let i=0;i<points.length;i++){
      if(!valid(t))return;
      const {node,p}=points[i];node.classList.add('active');node.querySelector('.step-state').textContent='ACTIVE';status(owner,node.textContent.replace(/\s+/g,' ').trim()+' / schematic execution.');
      if(!await wait(t,180))return;
      node.classList.remove('active');node.classList.add('visited');node.querySelector('.step-state').textContent='PASSED';
      if(i<points.length-1){
        const next=points[i+1],bypass=next.node.dataset.step-node.dataset.step>1;
        if(!await packet(t,owner.querySelector('svg'),bypass?[p,[3,p[1]],[3,next.p[1]],next.p]:[p,next.p],700))return;
      }
    }
    staticArchitecture(owner);state('observing',1800);finish(t);
  }
  for(const owner of all('[data-instrument="architecture"]')){
    owner.dataset.output='present';controllers.set(owner,()=>staticArchitecture(owner));
    for(const button of all('[data-output]',owner))button.addEventListener('click',()=>{
      settle();owner.dataset.output=button.dataset.output;
      all('[data-output]',owner).forEach(v=>v.setAttribute('aria-pressed',String(v===button)));
      staticArchitecture(owner);relocate(owner.id);
    });
    owner.querySelector('.play-trace').addEventListener('click',()=>playArchitecture(owner));
    staticArchitecture(owner);
  }
  function memoryMode(owner){return content.motion.memory.modes.find(v=>v.id===owner.dataset.mode);}
  function drawMemory(owner){
    const board=owner.querySelector('.memory-board'),plane=board.querySelector('svg'),r=board.getBoundingClientRect();
    plane.replaceChildren();plane.setAttribute('viewBox','0 0 '+Math.max(1,r.width)+' '+Math.max(1,r.height));
    owner._memoryPoints={};
    for(const node of all('[data-tier]',owner))owner._memoryPoints[node.dataset.tier]=[12,node.offsetTop+node.offsetHeight/2];
    const path=memoryMode(owner).path;
    for(let i=0;i<path.length-1;i++){const a=owner._memoryPoints[path[i]],b=owner._memoryPoints[path[i+1]];plane.append(svg('path',{d:'M '+a.join(' ')+' L '+b.join(' '),class:'selected'}));}
  }
  function staticMemory(owner){
    const mode=memoryMode(owner);owner.querySelector('.mode-note').textContent=mode.note;
    all('[data-tier]',owner).forEach(node=>{node.classList.toggle('selected',mode.path.includes(node.dataset.tier));node.classList.remove('active');});
    status(owner,mode.path.map(id=>content.motion.memory.tiers.find(v=>v.id===id).name).join(' → ')+' / conceptual path.');
    drawMemory(owner);
  }
  async function playMemory(owner){
    staticMemory(owner);relocate('memory-geography','working');
    const t=begin(owner,()=>all('.active',owner).forEach(v=>v.classList.remove('active')));if(!t)return;
    const path=memoryMode(owner).path;
    for(let i=0;i<path.length;i++){
      const node=owner.querySelector('[data-tier="'+path[i]+'"]');node.classList.add('active');
      status(owner,node.querySelector('b').textContent+' / illustrative workload location.');
      if(!await wait(t,220))return;node.classList.remove('active');
      if(i<path.length-1&&!await packet(t,owner.querySelector('svg'),[owner._memoryPoints[path[i]],owner._memoryPoints[path[i+1]]],700))return;
    }
    staticMemory(owner);finish(t);
  }
  const memory=document.getElementById('memory-geography');
  if(memory){
    memory.dataset.mode=content.motion.memory.modes[0].id;controllers.set(memory,()=>staticMemory(memory));staticMemory(memory);
    memory.querySelector('.play-trace').addEventListener('click',()=>playMemory(memory));
    all('[data-mode]',memory).forEach(button=>button.addEventListener('click',()=>{settle();memory.dataset.mode=button.dataset.mode;all('[data-mode]',memory).forEach(v=>v.setAttribute('aria-pressed',String(v===button)));staticMemory(memory);relocate('memory-geography');}));
  }
  const fabric=document.getElementById('fabric-console');
  function fabricPoints(){return innerWidth<650?{g0:[25,12],g1:[75,12],g2:[25,36],g3:[75,36],s0:[28,75],s1:[72,75]}:{g0:[12.5,16],g1:[37.5,16],g2:[62.5,16],g3:[87.5,16],s0:[32,65],s1:[68,65]};}
  function fabricPaths(mode){
    if(mode==='normal')return [['g0','s0','g2'],['g1','s1','g3']];
    if(mode==='adaptive')return [['g0','s1','g3'],['g1','s1','g3'],['g2','s0','s1','g3']];
    return [['g0','s0','g3'],['g1','s0','g3'],['g2','s0','g3']];
  }
  function drawFabric(){
    if(!fabric)return;
    const plane=fabric.querySelector('svg'),p=fabricPoints();plane.replaceChildren();
    const selected=new Set();
    for(const route of fabricPaths(fabric.dataset.mode))for(let i=0;i<route.length-1;i++)selected.add([route[i],route[i+1]].sort().join(':'));
    for(let i=0;i<4;i++)for(let j=0;j<2;j++){
      const a='g'+i,b='s'+j;plane.append(svg('path',{d:'M '+p[a].join(' ')+' L '+p[b].join(' '),class:(fabric.dataset.mode==='collective'||selected.has([a,b].sort().join(':')))?'selected':''}));
    }
    plane.append(svg('path',{d:'M '+p.s0.join(' ')+' L '+p.s1.join(' '),class:fabric.dataset.mode==='adaptive'?'selected':''}));
  }
  function queue(n,pressure=false){all('.queue-cell',fabric).forEach((v,i)=>v.classList.toggle('filled',i<n));fabric.querySelector('.queue-glyph').classList.toggle('pressure',pressure);}
  function staticFabric(){
    if(!fabric)return;
    const mode=content.motion.fabric.modes.find(v=>v.id===fabric.dataset.mode);
    fabric.querySelector('.mode-note').textContent=mode.note;
    all('.active',fabric).forEach(v=>v.classList.remove('active'));
    queue(mode.id==='congestion'?5:mode.id==='incast'?3:mode.id==='adaptive'?3:0,mode.id==='congestion');
    status(fabric,mode.name+' / '+mode.note);drawFabric();
  }
  async function travelRoutes(t,routes){
    const p=fabricPoints(),plane=fabric.querySelector('svg');
    return Promise.all(routes.map(async route=>{
      fabric.querySelector('[data-node="'+route[0]+'"]').classList.add('active');
      const ok=await packet(t,plane,route.map(id=>p[id]),1100);
      if(ok)fabric.querySelector('[data-node="'+route.at(-1)+'"]').classList.add('active');return ok;
    }));
  }
  async function playFabric(){
    staticFabric();relocate('fabric-console','investigating');
    const t=begin(fabric,()=>all('.active',fabric).forEach(v=>v.classList.remove('active')));if(!t)return;
    queue(0);const mode=fabric.dataset.mode;
    if(mode==='collective'){
      status(fabric,'SCATTER / one worker distributes illustrative partitions.');
      if(!(await travelRoutes(t,[['g0','s0','g1'],['g0','s1','g2'],['g0','s1','g3']])).every(Boolean))return;
      status(fabric,'LOCAL WORK / workers operate independently.');if(!await wait(t,700))return;
      status(fabric,'REDUCE / illustrative contributions converge.');
      if(!(await travelRoutes(t,[['g1','s0','g0'],['g2','s1','g0'],['g3','s1','g0']])).every(Boolean))return;
      status(fabric,'SYNCHRONIZE / the conceptual barrier releases.');all('.worker',fabric).forEach(v=>v.classList.add('active'));
      if(!await wait(t,650))return;
    }else{
      status(fabric,mode==='normal'?'Two independent flows / paths in motion.':'Three flows / converging on GPU 3.');
      if(!(await travelRoutes(t,fabricPaths(mode))).every(Boolean))return;
      if(mode!=='normal'){queue(3);status(fabric,'Receiver pressure / synchronized arrivals share a queue.');if(!await wait(t,500))return;}
      if(mode==='congestion'){status(fabric,'Another illustrative burst / pressure accumulates at the receiver.');if(!(await travelRoutes(t,fabricPaths(mode))).every(Boolean))return;queue(5,true);status(fabric,'Full illustrative queue / next arrival rejected.');state('alert',1700);if(!await wait(t,850))return;}
      if(mode==='adaptive'){status(fabric,'Alternate links selected / shared receiver bottleneck remains.');if(!await wait(t,850))return;}
    }
    staticFabric();state('observing',1800);finish(t);
  }
  if(fabric){
    fabric.dataset.mode=content.motion.fabric.modes[0].id;controllers.set(fabric,staticFabric);staticFabric();
    fabric.querySelector('.play-trace').addEventListener('click',playFabric);
    all('[data-mode]',fabric).forEach(button=>button.addEventListener('click',()=>{settle();fabric.dataset.mode=button.dataset.mode;all('[data-mode]',fabric).forEach(v=>v.setAttribute('aria-pressed',String(v===button)));staticFabric();relocate('fabric-console');}));
  }
  async function playFailure(owner){
    const repaired=owner.dataset.resolved==='true',known=owner.dataset.knownMotion==='true',nodes=all('[data-failure-step]',owner);
    relocate(owner.querySelector('[data-perch]').dataset.perch,'alert');
    const restore=()=>{owner.classList.toggle('repaired',repaired);owner.classList.toggle('broken',!repaired);nodes.forEach(v=>v.classList.remove('active'));status(owner,repaired?'Documented fix / resolved.':'Unresolved record / execution stops.');};
    const t=begin(owner,restore);if(!t){restore();return;}
    owner.classList.remove('broken','repaired');
    status(owner,known?'Host preference → image selection → rendered motion.':'Trigger → system → outcome.');
    nodes[0].classList.add('active');if(!await wait(t,650))return;nodes[0].classList.remove('active');nodes[1].classList.add('active');
    owner.classList.add('broken');status(owner,known?'Image boundary / motion preference did not reach the embedded animation. Browser internal cause unknown.':'Execution stops / inspect the documented symptom and evidence.');
    state('singed',1700);if(!await wait(t,1500))return;
    if(repaired){owner.classList.remove('broken');owner.classList.add('repaired');nodes[1].classList.remove('active');nodes[2].classList.add('active');status(owner,known?'Explicit host still-image selection / completed static rendering.':'Documented repair / trace reaches the outcome.');if(!await wait(t,850))return;}
    finish(t);
  }
  for(const owner of all('[data-instrument="failure"]'))owner.querySelector('.play-trace').addEventListener('click',()=>playFailure(owner));
  function drawDepth(){
    const board=document.querySelector('.depth-board');if(!board||!board.getClientRects().length)return;
    const plane=board.querySelector('svg'),r=board.getBoundingClientRect();plane.replaceChildren();plane.setAttribute('viewBox','0 0 '+r.width+' '+r.height);
    for(const [a,b] of content.depth.edges){
      const an=board.querySelector('[data-domain="'+a+'"]'),bn=board.querySelector('[data-domain="'+b+'"]');
      const ar=an.getBoundingClientRect(),br=bn.getBoundingClientRect();
      plane.append(svg('path',{d:'M '+(ar.left-r.left+ar.width/2)+' '+(ar.top-r.top+ar.height/2)+' L '+(br.left-r.left+br.width/2)+' '+(br.top-r.top+br.height/2),pathLength:1,'data-from':a,'data-to':b}));
    }
  }
  function selectDepth(id,explicit=false){
    const domain=content.depth.domains.find(v=>v.id===id);if(!domain)return;
    const connected=new Set([id]);for(const edge of content.depth.edges)if(edge.includes(id))edge.forEach(v=>connected.add(v));
    all('[data-domain]').forEach(node=>{node.setAttribute('aria-pressed',String(node.dataset.domain===id));node.classList.toggle('connected',connected.has(node.dataset.domain));node.classList.toggle('unrelated',!connected.has(node.dataset.domain));});
    all('.depth-board path').forEach(node=>node.classList.toggle('connected',node.dataset.from===id||node.dataset.to===id));
    document.getElementById('depth-note').textContent=domain.name+' / '+domain.state+'. '+domain.description+' Connected questions: '+content.depth.domains.filter(v=>v.id!==id&&connected.has(v.id)).map(v=>v.name).join(' · ')+'. '+content.depth.boundary;
    if(explicit){
      react('investigating');
      const board=document.querySelector('.depth-board'),t=begin(board);
      if(t){Promise.all(all('path.connected',board).map(node=>animate(t,node,[{strokeDasharray:'1',strokeDashoffset:'1'},{strokeDasharray:'1',strokeDashoffset:'0'}],850))).then(()=>finish(t));}
    }
  }
  all('[data-domain]').forEach(button=>{
    button.addEventListener('click',()=>selectDepth(button.dataset.domain,true));
    button.addEventListener('focus',()=>selectDepth(button.dataset.domain));
    button.addEventListener('pointerenter',()=>{if(matchMedia('(hover:hover)').matches)selectDepth(button.dataset.domain);});
  });
  async function animateCard(detail){
    const owner=detail.querySelector('.card-scene');if(!owner)return;
    const t=begin(owner,()=>owner.classList.remove('card-active'));if(!t)return;
    owner.classList.add('card-active');
    const id=detail.dataset.system;
    if(id==='cortex'){
      const layers=all('.cortex-layer',owner);await Promise.all(layers.map((node,i)=>animate(t,node,[{transform:'translateY(0)'},{transform:'translateY('+(i-2)*2+'px)'},{transform:'translateY(0)'}],1100)));
      if(valid(t)){const line=owner.querySelector('.signal');if(line)await animate(t,line,[{strokeDashoffset:'0'},{strokeDashoffset:'-40'}],900);}
    }else if(id==='argus'){
      const scan=owner.querySelector('.argus-scan'),pupil=owner.querySelector('.argus-pupil');
      if(scan)await animate(t,scan,[{transform:'translateY(-65px)',opacity:.1},{transform:'translateY(0)',opacity:.8}],1100);
      if(valid(t)&&pupil)await animate(t,pupil,[{opacity:.4},{opacity:1},{opacity:.4}],650);
    }else if(id==='fabric'){
      const paths=all('[data-route]',owner);await Promise.all(paths.map(node=>animate(t,node,[{strokeDashoffset:'0'},{strokeDashoffset:'-70'}],1400)));
    }else{
      const wave=owner.querySelector('.aegis-wave'),spike=owner.querySelector('.aegis-anomaly');
      if(wave)await animate(t,wave,[{strokeDasharray:'1',strokeDashoffset:'1'},{strokeDasharray:'1',strokeDashoffset:'0'}],1100);
      if(valid(t)&&spike)await animate(t,spike,[{opacity:.3},{opacity:1},{opacity:.3}],650);
    }
    finish(t);
  }
  for(const detail of all('.system')){
    let last=0;
    detail.addEventListener('pointerenter',event=>{
      if(!matchMedia('(hover:hover)').matches)return;
      const r=detail.getBoundingClientRect(),x=event.clientX-r.left,y=event.clientY-r.top;
      const distances=[['left',x],['right',r.width-x],['top',y],['bottom',r.height-y]].sort((a,b)=>a[1]-b[1]);detail.dataset.entry=distances[0][0];
      if(Date.now()-last>4000){last=Date.now();animateCard(detail);}
    });
    detail.addEventListener('pointerleave',()=>delete detail.dataset.entry);
    detail.addEventListener('toggle',()=>{
      if(detail.open){relocate('flow-'+detail.dataset.system,'working');controllers.get(detail.querySelector('.architecture'))?.();animateCard(detail);}
      else if(task&&detail.contains(task.owner))settle();
    });
  }
  for(const detail of all('.record'))detail.addEventListener('toggle',()=>{
    if(!detail.open){if(task&&detail.contains(task.owner))settle();return;}
    if(detail.classList.contains('failure'))relocate('failure-'+detail.id,'alert');
    else react(detail.classList.contains('experiment')?'working':'observing');
    detail.querySelector('.record-plot')?.classList.add('trace-reveal');
  });
  async function probeCore(){
    const owner=document.querySelector('.hero-scene');if(!owner)return;
    owner.classList.add('core-selected');document.getElementById('core-state').textContent='Ω / SIGNAL RECEIVED · a conceptual scan enters the core.';
    const t=begin(owner,()=>{owner.classList.remove('core-notice');document.getElementById('core-state').textContent='Ω / SIGNAL SETTLED · the core holds; the surrounding machinery rests.';});
    if(!t)return;
    owner.classList.add('core-notice');state('observing',2000);
    if(await wait(t,1500))finish(t);
  }
  document.querySelector('.core-control')?.addEventListener('click',probeCore);
  function scheduleCore(){
    clearTimeout(coreTimer);
    if(!canMove())return;
    coreTimer=setTimeout(()=>{if(!task&&!root.classList.contains('scroll-moving')&&inView(document.querySelector('.hero-scene')))probeCore();scheduleCore();},31000);
  }
  function updateDescent(){
    const rail=all('[data-descent]');let active=rail[0];
    for(const link of rail){const target=document.querySelector(link.hash);if(target&&target.getBoundingClientRect().top<innerHeight*.45)active=link;}
    rail.forEach(link=>{if(link===active)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');});
    const layer=active?.dataset.descent||'INTENT';root.dataset.depth=layer;document.getElementById('active-layer').textContent=layer;
  }
  if('IntersectionObserver' in window){
    const observer=new IntersectionObserver(entries=>{
      for(const entry of entries){
        const node=entry.target;node.classList.toggle('motion-visible',entry.isIntersecting);
        if(entry.isIntersecting){visible.add(node);if(node.classList.contains('section')&&!node.dataset.revealed){node.dataset.revealed='true';node.classList.add('trace-reveal');}controllers.get(node)?.();}
        else{visible.delete(node);if(task&&(node===task.owner||node.contains(task.owner)))settle();}
      }
    },{threshold:0});
    new Set(all('.scene,.instrument,.pet,.section,.telemetry')).forEach(node=>observer.observe(node));
    const perches=new IntersectionObserver(entries=>{for(const entry of entries)if(entry.isIntersecting&&entry.target.dataset.perch==='channel'&&!terminalActive)relocate('channel','observing');});
    const channel=document.querySelector('[data-perch="channel"]');if(channel)perches.observe(channel);
  }else all('.scene,.pet').forEach(node=>node.classList.add('motion-visible'));
  function setMotion(value){
    stopped=value||reduced.matches;settle();
    if(stopped){clearTimeout(coreTimer);resident.getAnimations().forEach(a=>a.cancel());}
    else scheduleCore();
    for(const refresh of controllers.values())refresh();
  }
  function terminal(value){
    terminalActive=value;
    if(value){priorPerch=resident.closest('[data-perch]')?.dataset.perch||'home';relocate('terminal','observing');}
    else{terminalActive=false;relocate(priorPerch,'idle',true);}
  }
  async function dragonCommand(){
    state('investigating',2200);
    const zone=resident.closest('[data-perch]'),t=begin(zone,()=>state('idle'));if(!t)return;
    const dot=document.createElement('span');dot.className='carried-packet';dot.setAttribute('aria-hidden','true');zone.append(dot);t.nodes.push(dot);
    await animate(t,dot,[{transform:'translate(12px,8px)',opacity:0},{transform:'translate(40px,8px)',opacity:1},{transform:'translate(90px,8px)',opacity:0}],1400);finish(t);
  }
  // Styles belong to the hashed stylesheet; avoid dynamic inline style.
  window.VoidLab={react,resetIdle,setMotion,terminal,dragonCommand,settle};
  document.addEventListener('pointerdown',resetIdle,{passive:true});document.addEventListener('keydown',resetIdle);
  document.addEventListener('scroll',()=>{root.classList.add('scroll-moving');clearTimeout(scrollTimer);scrollTimer=setTimeout(()=>{root.classList.remove('scroll-moving');updateDescent();},220);resetIdle();},{passive:true});
  window.addEventListener('resize',()=>{if(task)settle();for(const refresh of controllers.values())refresh();drawDepth();updateDescent();});
  document.addEventListener('visibilitychange',()=>{
    root.classList.toggle('page-away',document.hidden);
    if(document.hidden){settle();clearTimeout(coreTimer);clearTimeout(idleTimer);resident.getAnimations().forEach(a=>a.cancel());state('sleeping');}
    else{state('idle');resetIdle();scheduleCore();}
  });
  resident.querySelector('.resident-touch').addEventListener('click',()=>react('observing'));
  requestAnimationFrame(()=>{drawDepth();updateDescent();for(const refresh of controllers.values())refresh();});
  resetIdle();scheduleCore();
})();
