"""Small, source-backed graphics for the existing static laboratory (stdlib)."""
from html import escape
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
RULES=[]
NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)
def e(v):return escape(str(v),quote=True)
def perch(name,home=False):
    return f'<div class="dragon-perch" data-perch="{e(name)}"'+('' if home else ' aria-hidden="true"')+'></div>'
def inline_art(name,identity):
    tree=ET.fromstring((ROOT/'assets'/name).read_text())
    for parent in tree.iter():
        for child in list(parent):
            if child.tag.split('}')[-1] in {'style','title','desc'}:
                if child.tag.endswith('style'):RULES.append(child.text or '')
                parent.remove(child)
    ids={node.attrib['id']:identity+'-'+node.attrib['id'] for node in tree.iter() if 'id' in node.attrib}
    for i,node in enumerate(tree.iter()):
        if 'id' in node.attrib:node.attrib['id']=ids[node.attrib['id']]
        for attr,value in list(node.attrib.items()):
            for old,new in ids.items():value=value.replace('url(#'+old+')','url(#'+new+')')
            node.attrib[attr]=value
        if 'style' in node.attrib:
            cls=identity+'-style-'+str(i)
            RULES.append('.'+cls+'{'+node.attrib.pop('style')+'}')
            node.attrib['class']=node.attrib.get('class','')+' '+cls
        node.attrib.pop('aria-label',None)
    tree.attrib.update({'class':'inline-art','aria-hidden':'true','focusable':'false'})
    tree.attrib.pop('role',None);tree.attrib.pop('aria-labelledby',None)
    return ET.tostring(tree,encoding='unicode')
def artwork_css():return '\n'.join(dict.fromkeys(RULES))
def hero(picture):
    return '<div class="hero-art"><div class="hero-scene scene" data-scene="core"><div class="art-fallback">'+picture+'</div><div class="art-inline scene-desktop">'+inline_art('observatory.svg','hero-desktop')+'</div><div class="art-inline scene-mobile">'+inline_art('observatory-mobile.svg','hero-mobile')+'</div><button class="core-control enhancement" type="button" aria-label="Probe the Omega core"><span class="sr-only">Probe Ω</span></button><div class="core-scan" aria-hidden="true"></div></div></div><p id="core-state" class="micro" role="status">Ω / CONCEPTUAL CORE · the surrounding machinery is at rest.</p>'
def card(name,identity,picture):
    return '<span class="card-scene scene" data-scene="'+e(identity)+'"><span class="art-fallback">'+picture+'</span><span class="art-inline">'+inline_art(name,'card-'+identity)+'</span><span class="card-trace" aria-hidden="true"></span></span>'
def rail(data):
    items=''.join(f'<a href="#{e(target)}" data-descent="{e(label)}"><span class="rail-dot" aria-hidden="true"></span>{e(label)}</a>' for label,target in data['rail'])
    return '<aside class="execution-rail enhancement" aria-label="Conceptual execution layers"><p class="micro">EXECUTION TRACE</p><div class="rail-links">'+items+'</div><div class="rail-controls"><span id="active-layer" class="micro">INTENT</span><button class="motion-short" type="button" aria-pressed="false">Pause motion</button></div></aside>'
def foot(button,zone,status):
    return '<div class="instrument-foot"><div class="instrument-actions">'+button+'<p class="trace-status micro" role="status">'+e(status)+'</p></div>'+perch(zone)+'</div>'
def flow(system,standalone=False):
    identity=('runtime' if standalone else 'flow-'+system['id'])
    nodes=list(system['architecture'])
    if system['id']=='argus':nodes.append('Returned trace')
    rows=''.join(f'<li data-step="{i}"'+(' data-memory="true"' if system['id']=='argus' and label=='JSONL memory' else '')+f'><span class="step-index">{i+1:02d}</span><span>{e(label)}</span><span class="step-state micro">READY</span></li>' for i,label in enumerate(nodes))
    choices='<div class="mode-controls" role="group" aria-label="Provider output example"><button type="button" data-output="present" aria-pressed="true">Non-empty text</button><button type="button" data-output="empty" aria-pressed="false">Empty text</button></div>' if system['id']=='argus' else ''
    boundary='Source-linked schematic. The output check tests non-empty text; it does not verify correctness. No provider or tool is executed.' if system['id']=='argus' else 'Conceptual architecture scope. This playback does not imply an operational integration.'
    status='Select an example, then play the source path.' if system['id']=='argus' else 'Inspect the conceptual sequence.'
    return f'<div class="instrument architecture" id="{identity}" data-system="{e(system["id"])}" data-instrument="architecture">{choices}<div class="trace-board"><svg class="wire-plane" aria-hidden="true"></svg><ol class="trace-steps">{rows}</ol></div><p class="boundary">{boundary}</p>'+foot('<button class="play-trace enhancement" type="button">Play trace ↘</button>',identity,status)+'</div>'
def runtime(data):
    system=next((s for s in data['systems'] if s['id']=='argus'),None)
    if not system:return ''
    return '<section id="runtime-playback" class="subsection lab-console" aria-labelledby="runtime-title"><p class="eyebrow">EXECUTION / SOURCE CONTRACT</p><h3 id="runtime-title">Follow a request through ARGUS.</h3><p>One path. One deliberately small verification test. Inspect the empty-output branch.</p>'+flow(system,True)+'</section>'
def fabric(data):
    modes=''.join(f'<button type="button" data-mode="{e(v["id"])}" aria-pressed="{str(i==0).lower()}">{e(v["name"])}</button>' for i,v in enumerate(data['modes']))
    labels=''.join(f'<div class="fabric-node worker" data-node="g{i}"><span class="micro">WORKER / {i:02d}</span><b>GPU {i}</b><span class="node-light" aria-hidden="true"></span></div>' for i in range(4))
    labels+=''.join(f'<div class="fabric-node switch" data-node="s{i}"><b>FABRIC {i}</b></div>' for i in range(2))
    queue=''.join('<span class="queue-cell"></span>' for _ in range(5))
    return '<section id="fabric-console" class="subsection lab-console instrument" data-instrument="fabric" aria-labelledby="fabric-title"><p class="eyebrow">FABRIC / CONCEPTUAL DEMONSTRATION</p><h3 id="fabric-title">Communication is part of the computer.</h3><div class="mode-controls" role="group" aria-label="Communication mode">'+modes+'</div><div class="fabric-board"><svg class="wire-plane" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"></svg>'+labels+'</div><div class="queue-glyph" aria-hidden="true"><span>RECEIVER QUEUE</span>'+queue+'</div><p class="mode-note">'+e(data['modes'][0]['note'])+'</p><p class="boundary">'+e(data['boundary'])+'</p>'+foot('<button class="play-trace enhancement" type="button">Play flow ↘</button>','fabric-console','Normal / paths ready.')+'</section>'
def memory(data):
    modes=''.join(f'<button type="button" data-mode="{e(v["id"])}" aria-pressed="{str(i==0).lower()}">{e(v["name"])}</button>' for i,v in enumerate(data['modes']))
    nodes=''.join(f'<li data-tier="{e(v["id"])}"><span class="micro">{e(v["zone"])}</span><b>{e(v["name"])}</b><span>{e(v["role"])}</span></li>' for v in data['tiers'])
    return '<section id="memory-geography" class="subsection lab-console instrument" data-instrument="memory" aria-labelledby="memory-title"><p class="eyebrow">COMPUTE / MEMORY GEOGRAPHY</p><h3 id="memory-title">Memory has geography.</h3><div class="mode-controls" role="group" aria-label="Memory path">'+modes+'</div><div class="memory-board"><svg class="wire-plane" aria-hidden="true"></svg><ol class="memory-tiers">'+nodes+'</ol></div><p class="mode-note">'+e(data['modes'][0]['note'])+'</p><p class="boundary">'+e(data['boundary'])+'</p>'+foot('<button class="play-trace enhancement" type="button">Send workload ↗</button>','memory-geography','Model artifact / ready to transfer.')+'</section>'
def telemetry(count):
    marks=''.join(f'<rect x="{6+i*9}" y="10" width="4" height="4"/>' for i in range(min(count,24)))
    return f'<svg class="count-trace" viewBox="0 0 224 24" aria-hidden="true"><path d="M 2 12 H 220" pathLength="1"/>{marks}</svg>'
def plot(item,data):
    samples=[]
    for ref in item.get('relatedExperiments',[]):
        experiment=next((v for v in data['experiments'] if v['id']==ref),None)
        if not experiment:continue
        metric=next((v for v in experiment.get('measurements',[]) if v['label']=='Delivered-packet p99'),None)
        loss=next((v for v in experiment.get('measurements',[]) if v['label']=='Dropped / sent'),None)
        if metric and isinstance(metric['value'],(int,float)) and experiment.get('source'):samples.append((experiment,metric,loss))
    if samples:
        maximum=max(v[1]['value'] for v in samples) or 1
        rows=''
        for record,metric,loss in samples:
            value=metric['value'];width=value/maximum*190
            rows+=f'<div class="plot-row"><span>{e(record["id"])}</span><svg viewBox="0 0 200 20" aria-hidden="true"><path d="M 1 10 H {width:.2f}" pathLength="1"/></svg><b>{e(value)} {e(metric["unit"])}</b><small>DROPPED / {e(loss["value"] if loss else "not recorded")}</small></div>'
        return '<figure class="record-plot"><figcaption>DELIVERED-PACKET p99 / SYNTHETIC MODEL</figcaption>'+rows+'<p class="micro">Accepted packets only. Compare delivery alongside the tail. Bars use linked records; no hardware run.</p></figure>'
    if item['system']=='argus' and item.get('type')=='source-review':
        return '<figure class="record-plot contract-outcomes"><figcaption>OUTPUT CHECK / SOURCE CONTRACT</figcaption><div>Empty text <span aria-hidden="true">→</span> <b>Memory skipped</b></div><div>Non-empty text <span aria-hidden="true">→</span> <b>Memory write path</b></div><p class="micro">Illustrated source behavior. No provider run or semantic correctness is implied.</p></figure>'
    return ''
def failure(item):
    labels=['Preference','Image selection','Rendered motion'] if item['id']=='F-001' else ['Trigger','System','Outcome']
    nodes=''.join(f'<li data-failure-step="{i}">{e(label)}<span class="failure-mark" aria-hidden="true">×</span></li>' for i,label in enumerate(labels))
    repaired=item['status']=='RESOLVED'
    return f'<div class="failure-instrument instrument'+(' repaired' if repaired else ' broken')+f'" data-instrument="failure" data-known-motion="{str(item["id"]=="F-001").lower()}" data-resolved="{str(repaired).lower()}"><ol class="failure-path">{nodes}</ol>'+foot('<button class="play-trace enhancement" type="button">Inspect failure trace ↘</button>','failure-'+item['id'],'Documented fix / resolved.' if repaired else 'Unresolved record / execution stops.')+'</div>'
def depth(data):
    nodes=''.join(f'<button type="button" class="depth-node enhancement" data-domain="{e(v["id"])}" aria-pressed="false"><span class="micro">{e(v["state"])}</span><b>{e(v["name"])}</b></button>' for v in data['domains'])
    fallback=''.join(f'<article class="domain"><h4>{e(v["name"])}</h4><span class="micro">{e(v["state"])}</span><p>{e(v["description"])}</p></article>' for v in data['domains'])
    return '<div class="depth-machine"><div class="depth-board"><svg class="wire-plane" aria-hidden="true"></svg>'+nodes+'</div><div id="depth-note" class="depth-note" role="status">Choose a domain to inspect its connections. '+e(data['boundary'])+'</div><div class="depth-fallback depth-grid">'+fallback+'</div></div>'
def geometry_css(data):
    rules=[]
    for mode,columns,field in [('mobile',2,'mobile'),('desktop',3,'desktop')]:
        rows=max(v[field][1] for v in data['domains'])+1
        s=f'.depth-board{{grid-template-columns:repeat({columns},minmax(0,1fr));grid-template-rows:repeat({rows},112px)}}'
        for node in data['domains']:
            x,y=node[field]
            s+=f'.depth-node[data-domain="{node["id"]}"]{{grid-column:{x+1};grid-row:{y+1}}}'
        rules.append('@media(min-width:760px){'+s+'}' if mode=='desktop' else s)
    return '\n'.join(rules)
def readme_graphics():
    def asset(name,title,labels,desc):
        height=92+len(labels)*53
        rows=''.join(f'<circle cx="30" cy="{87+i*53}" r="4" fill="#bdacff"/><text x="55" y="{92+i*53}" fill="#f1eef8" font-family="monospace" font-size="16">{e(label)}</text>' for i,label in enumerate(labels))
        path=f'M 30 87 V {87+(len(labels)-1)*53}'
        css='<style>.pulse{stroke-dasharray:18 700;animation:trace 4s linear 1 forwards}@keyframes trace{to{stroke-dashoffset:-700;opacity:0}}@media(prefers-reduced-motion:reduce){.pulse{display:none}}</style>'
        body=f'<svg xmlns="{NS}" width="400" height="{height}" viewBox="0 0 400 {height}" role="img"><title>{e(title)}</title><desc>{e(desc)}</desc>{css}<rect width="400" height="{height}" rx="12" fill="#090810"/><text x="24" y="35" fill="#bdacff" font-family="monospace" font-size="13">{e(title)}</text><path d="{path}" stroke="#4f415e" fill="none"/><path class="pulse" d="{path}" stroke="#bdacff" stroke-width="2" fill="none"/>{rows}<text x="24" y="{height-15}" fill="#aaa3b9" font-family="monospace" font-size="11">SCHEMATIC / NO LIVE SERVICE OR TIMING</text></svg>\n'
        still=re.sub(r'<style>.*?</style>','',body,flags=re.S)
        still=re.sub(r'<path class="pulse"[^>]*/>','',still)
        return {f'assets/{name}.svg':body,f'assets/still/{name}.svg':still}
    result={}
    result.update(asset('lab-execution','ARGUS / OUTPUT CONTRACT',['Request → intent → plan','Route → provider → output check','Empty? Skip JSONL memory','Non-empty? Write JSONL memory','Return trace / presence ≠ correctness'],'Source-backed ARGUS output contract, no inference is run.'))
    routes=['M 50 108 L 175 190 V 265','M 175 108 V 265','M 300 108 L 175 190 V 265']
    lines=''.join(f'<path d="{path}" fill="none" stroke="#594665"/><path class="pulse" d="{path}" fill="none" stroke="#bdacff" stroke-width="2"/>' for path in routes)
    workers=''.join(f'<rect x="{x-38}" y="66" width="76" height="42" rx="4" fill="#090810" stroke="#78608e"/><text x="{x}" y="92" text-anchor="middle" font-family="monospace" font-size="16" fill="#f1eef8">GPU {i}</text>' for i,x in enumerate([50,175,300]))
    fabric=f'<svg xmlns="{NS}" width="400" height="370" viewBox="0 0 400 370" role="img"><title>Conceptual incast</title><desc>Three senders converge on one receiver. The geometry and signal timing are illustrative.</desc><style>.pulse{{stroke-dasharray:8 500;animation:arrive 4s linear 1 forwards}}@keyframes arrive{{to{{stroke-dashoffset:-500;opacity:0}}}}@media(prefers-reduced-motion:reduce){{.pulse{{display:none}}}}</style><rect width="400" height="370" rx="12" fill="#090810"/><text x="24" y="35" fill="#bdacff" font-family="monospace" font-size="13">FABRIC / CONCEPTUAL INCAST</text>{lines}{workers}<rect x="120" y="171" width="110" height="38" rx="4" fill="#090810" stroke="#78608e"/><text x="175" y="195" text-anchor="middle" fill="#f1eef8" font-family="monospace" font-size="15">FABRIC</text><rect x="123" y="265" width="104" height="42" rx="4" fill="#090810" stroke="#bdacff"/><text x="175" y="292" text-anchor="middle" fill="#f1eef8" font-family="monospace" font-size="16">GPU 3</text><text x="24" y="343" fill="#aaa3b9" font-family="monospace" font-size="12">CONVERGENCE / NO HARDWARE MEASUREMENT</text></svg>\n'
    result['assets/lab-fabric.svg']=fabric
    still=re.sub(r'<style>.*?</style>','',fabric,flags=re.S)
    result['assets/still/lab-fabric.svg']=re.sub(r'<path class="pulse"[^>]*/>','',still)
    result.update(asset('lab-memory','MEMORY / MODEL LOADING',['Storage / persisted model','System RAM / staging','Interconnect / transfer','VRAM / device residency'],'A conceptual loading path; no numerical latency values.'))
    return result
