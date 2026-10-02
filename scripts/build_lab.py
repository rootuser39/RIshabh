#!/usr/bin/env python3
"""Validate shared research records and render the HTML + README views (stdlib)."""

import argparse
import base64
from datetime import date
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlparse

from void_dragon import DRAGON_CSS, dragon

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('site', 'current-signal', 'systems', 'experiments', 'field-logs', 'failures',
         'questions', 'tools', 'depth', 'transmissions', 'map', 'sources')
STATES = {'UNEXPLORED', 'ORIENTING', 'ACTIVE', 'OPERATIONAL', 'BUILT WITH'}
FAILURE_STATES = {'OPEN', 'INVESTIGATING', 'UNDERSTOOD', 'RESOLVED'}


def esc(value):
    return escape(str(value), quote=True)


def valid_url(value):
    parsed = urlparse(value)
    if parsed.scheme:
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError(f'Unsafe content URL: {value}')
    elif value.startswith('//') or '\\' in value or any(part == '..' for part in value.split('/')):
        raise ValueError(f'Unsafe relative URL: {value}')
    return value


def load_content():
    data = {name: json.loads((ROOT / 'content' / f'{name}.json').read_text()) for name in NAMES}
    systems = {item['id'] for item in data['systems']} | {'observatory'}
    for name in ('systems', 'experiments', 'field-logs', 'failures', 'questions', 'transmissions'):
        identifiers = [item['id'] for item in data[name]]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError(f'Duplicate IDs in {name}')
        for item in data[name]:
            if not re.fullmatch(r'[a-zA-Z0-9-]+', item['id']):
                raise ValueError(f'Invalid ID: {item["id"]}')
            if item.get('system') and item['system'] not in systems:
                raise ValueError(f'Unknown system in {name}: {item["system"]}')
            if item.get('date'):
                date.fromisoformat(item['date'])
    for item in data['experiments']:
        if item['type'] not in {'synthetic', 'measured', 'planned'}:
            raise ValueError(f'Experiment {item["id"]} needs an evidence type')
        if item.get('measurements') and (item['type'] == 'planned' or not item.get('source')):
            raise ValueError('Measurements require observed provenance, not a plan')
        for metric in item.get('measurements', []):
            if not metric.get('label') or not metric.get('unit'):
                raise ValueError('Every metric needs a label and unit')
    for item in data['field-logs']:
        for experiment in item.get('relatedExperiments', []):
            if experiment not in {e['id'] for e in data['experiments']}:
                raise ValueError(f'Unknown related experiment: {experiment}')
    if data['current-signal'].get('latestExperiment') not in {e['id'] for e in data['experiments']} | {None}:
        raise ValueError('Latest experiment must reference a real record')
    for item in data['failures']:
        if item['status'] not in FAILURE_STATES:
            raise ValueError('Unknown failure status')
    for item in data['tools'] + data['depth']['domains']:
        if item['state'] not in STATES:
            raise ValueError('Unknown exploration state')
    for layer in data['map']['layers']:
        if any(item not in systems for item in layer['systems']):
            raise ValueError('Unknown system in layer map')
    for system in data['systems']:
        if system.get('asset') and not re.fullmatch(r'[a-zA-Z0-9_-]+\.svg',system['asset']):
            raise ValueError('Asset names must be local SVG basenames')
        if system.get('asset') and not (ROOT / 'assets' / system['asset']).is_file():
            raise ValueError(f'Missing card asset: {system["asset"]}')
        if any(item not in {f['id'] for f in data['failures']} for item in system.get('failures', [])):
            raise ValueError('Unknown system failure reference')
    date.fromisoformat(data['current-signal']['updated'])
    date.fromisoformat(data['sources']['reviewed'])
    if data['site']['hosting']['enabled'] and not data['site']['hosting'].get('url'):
        raise ValueError('Enabled hosting requires a verified URL')
    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == 'url' and child:
                    valid_url(child)
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(data)
    return data


def link(item):
    return f'<a href="{esc(valid_url(item["url"]))}">{esc(item["label"])} ↗</a>'


def links(items):
    return '<div class="evidence-links">' + ''.join(link(item) for item in items) + '</div>'


def field(label, html):
    return f'<div class="field"><dt>{esc(label)}</dt><dd>{html}</dd></div>'


def fields(items):
    return '<dl class="fields">' + ''.join(field(label, html) for label, html in items) + '</dl>'


def listing(items, fallback='Not yet documented.'):
    return '<ul>' + ''.join(f'<li>{esc(item)}</li>' for item in items) + '</ul>' if items else esc(fallback)


def picture(name, alt='', card=False, closing=False):
    mobile = name.replace('.svg', '-mobile.svg') if name in {'observatory.svg', 'void-footer.svg'} else None
    sources = ''
    if mobile:
        media = '(prefers-reduced-motion: reduce) and (max-width: 640px)'
        sources += f'<source media="{media}" data-motion-media="{media}" srcset="assets/still/{mobile}">'
    media = '(prefers-reduced-motion: reduce)'
    sources += f'<source media="{media}" data-motion-media="{media}" srcset="assets/still/{name}">'
    if mobile:
        sources += f'<source media="(max-width: 640px)" srcset="assets/{mobile}">'
    w, h = (560, 240) if card else (1200, 214) if closing else (1200, 650)
    loading = 'loading="lazy"' if card or closing else 'fetchpriority="high"'
    classes = 'class="system-art"' if card else ''
    return f'<picture>{sources}<img src="assets/{esc(name)}" width="{w}" height="{h}" alt="{esc(alt)}" {loading} {classes}></picture>'


def section(identifier, number, label, title, intro, body):
    return f'<section id="{identifier}" class="section" aria-labelledby="{identifier}-title"><header class="section-head"><p class="eyebrow">{number} / {esc(label)}</p><h2 id="{identifier}-title">{esc(title)}</h2><p>{esc(intro)}</p></header>{body}</section>'


def system_name(data, identifier):
    return next((s['name'] for s in data['systems'] if s['id'] == identifier), 'VOID OBSERVATORY')


def chips(data, identifiers):
    return '<div class="chips">' + ''.join(f'<a class="chip" href="#system-{esc(i)}">{esc(system_name(data,i))}</a>' for i in identifiers if i != 'observatory') + '</div>'


def metrics(items):
    result = []
    for item in items:
        value = '<span class="not-completed">Not completed</span>' if item['value'] is None else esc(item['value']) + f'<span class="unit">{esc(item["unit"])}</span>'
        result.append(f'<div><dt>{esc(item["label"])}</dt><dd>{value}</dd></div>')
    return '<dl class="metrics">' + ''.join(result) + '</dl>' if result else ''


def record(item, kind, body):
    state = item.get('status', item.get('type', 'record')).upper()
    meta = f'{kind} / {item["id"]} · {item.get("date") or "DATE NOT DOCUMENTED"} · {state}'
    return f'<details id="{esc(item["id"])}" class="record {kind.lower().replace(" ","-")}" data-system="{esc(item["system"])}"><summary><span class="record-meta">{esc(meta)}</span><span class="record-title">{esc(item["title"])}</span></summary><div class="record-body">{body}</div></details>'


def empty(label, description):
    return f'<div class="empty"><p class="eyebrow">{esc(label)}</p><p>{esc(description)}</p></div>'


def render_body(data, derived):
    site, signal = data['site'], data['current-signal']
    parts = [f'<section id="identity" aria-label="Identity"><div class="hero-art" aria-hidden="true">{picture("observatory.svg")}</div><div class="intro"><p class="eyebrow">ARCHITECT. ARTIST. SCIENTIST.</p><h1>{esc(site["statement"])}</h1><p>I’m {esc(site["name"])} {esc(site["intro"])}</p><p class="signature"><b>Architect</b> the system. <b>Study</b> the mechanism. <b>Make</b> something worth looking at.</p></div></section>']
    signal_fields = [(label.upper(), esc(signal[key])) for key,label in [('building','Building'),('investigating','Investigating'),('breaking','Breaking'),('learning','Learning')]]
    latest = next((e for e in data['experiments'] if e['id'] == signal.get('latestExperiment')), None)
    signal_fields += [('LATEST EXPERIMENT', f'<a href="#{latest["id"]}">{esc(latest["id"])} / {esc(latest["title"])}</a><br><span class="micro">Recorded {esc(latest["date"])} · {esc(latest["type"])}</span>' if latest else 'Not yet documented.'), ('LAST SHIPPED', f'<a href="{esc(signal["lastShipped"]["url"])}">{esc(signal["lastShipped"]["title"])}</a><br><span class="micro">{esc(signal["lastShipped"]["date"])}</span>')]
    signal_card = f'<div class="surface"><div class="signal-top"><span class="eyebrow">CURRENT SIGNAL / {esc(signal["updated"])}</span><span class="status">{esc(signal["status"])}</span></div>{fields(signal_fields)}<p class="signal-note">{esc(signal["mode"])}. “Updated” is the content edit date, not a hardware or activity heartbeat.</p></div>'
    pet = f'<aside class="surface pet-panel" aria-label="Void Dragon interface companion"><div class="pet-header"><p class="eyebrow">VOID DRAGON / 01</p><p class="pet-state" id="pet-state">IDLE</p></div><div class="pet-stage"><svg class="pet" data-state="idle" viewBox="0 0 76 63" aria-hidden="true" focusable="false">{dragon(8,4,1)}</svg></div><p class="signal-note">Curiosity, with a pulse. The companion reacts to records being opened.</p><div class="pet-controls enhancement"><button type="button" id="pet-observe">Observe</button><button type="button" id="motion-toggle" aria-pressed="false">Pause motion</button></div></aside>'
    counts = [('systems','SYSTEMS'),('experiments','EXPERIMENTS'),('fieldLogs','FIELD LOGS'),('failures','FAILURES'),('transmissions','TRANSMISSIONS')]
    telemetry = '<dl class="telemetry" aria-label="Content-derived record counts">' + ''.join(f'<div><dt>{label}</dt><dd>{derived["counts"][key]}</dd></div>' for key,label in counts) + '</dl><p class="telemetry-note">CONTENT TELEMETRY / counts from these records · source review ' + esc(data['sources']['reviewed']) + ' · no realtime monitoring.</p>'
    parts.append(section('signal','01','WORKING RECORD','Current signal','A small, maintained window into the work. Evidence and intent remain separate.',f'<div class="signal-layout">{signal_card}{pet}</div>{telemetry}'))
    panels=[]
    for system in data['systems']:
        art = picture(system['asset'], card=True) if system.get('asset') else f'<h3>{esc(system["name"])}</h3>'
        path = '<ol class="path">' + ''.join(f'<li>{esc(stage)}</li>' for stage in system['architecture']) + '</ol>'
        body = f'<h3>{esc(system["name"])}</h3><p>{esc(system["thesis"])}</p>' + fields([('QUESTION',esc(system['question'])),('WHY IT EXISTS',esc(system['why'])),('ARCHITECTURE',path),('CURRENT STATE',esc(system['state'])),('BUILT',listing(system['built'])),('CURRENTLY INVESTIGATING',esc(system['investigating'])),('NEXT EXPERIMENT',esc(system['nextExperiment'])),('FAILURE RECORDS', ' · '.join(f'<a href="#{esc(i)}">{esc(i)}</a>' for i in system.get('failures',[])) or 'No linked failures documented.')])
        body += links(system['evidence']) + f'<p class="boundary">{esc(system["boundary"])}</p>'
        panels.append(f'<details id="system-{system["id"]}" class="system" data-system="{system["id"]}"><summary><span class="sr-only">Inspect {esc(system["name"])}</span>{art}<span class="system-caption">{esc(system["state"])} / INSPECT</span></summary><div class="system-body">{body}</div></details>')
    relationships = ''.join(f'<article class="relationship"><p class="micro">{esc(r["kind"])}</p><h4>{esc(system_name(data,r["from"]))} ↔ {esc(system_name(data,r["to"]))}</h4><p>{esc(r["description"])}</p>{link(r["source"]) if r.get("source") else ""}</article>' for r in data['map']['relationships'])
    layers=''.join(f'<div class="layer"><span class="layer-index" aria-hidden="true">{i:02d}</span><div class="layer-content"><div class="layer-title"><span class="layer-label">{esc(layer["name"])}</span><button class="enhancement" type="button" data-layer="{esc(layer["id"])}" aria-pressed="false">{esc(layer["name"])}</button>{chips(data,layer["systems"])}</div><p>{esc(layer["question"])}</p></div></div>' for i,layer in enumerate(data['map']['layers'],1))
    map_html=f'<div class="surface map"><header class="map-head"><p class="eyebrow">RELATIONSHIPS / THE LAYERS BENEATH</p><h3>Follow the execution path.</h3><p>{esc(data["map"]["boundary"])}</p></header><div class="relationship-grid">{relationships}</div><div class="layers">{layers}</div><p id="layer-note" class="layer-note" aria-live="polite">{esc(data["map"]["boundary"])}</p></div>'
    parts.append(section('systems','02','SYSTEMS IN ORBIT','Inspectable systems','Open a panel to inspect the question, the implementation and the unresolved boundary.', '<div class="system-grid">'+''.join(panels)+'</div>'+map_html))
    evidence_systems=list(dict.fromkeys(item['system'] for name in ('experiments','field-logs','failures') for item in data[name]))
    choices=[('all','All records')]+[(identifier,system_name(data,identifier)) for identifier in evidence_systems]
    filters='<div class="filters" role="group" aria-label="Filter evidence by system">'+''.join(f'<button type="button" data-filter-group="evidence" data-filter="{identifier}" aria-pressed="{str(identifier=="all").lower()}">{label}</button>' for identifier,label in choices)+'</div><p id="evidence-count" class="sr-only" aria-live="polite"></p>'
    records=[]
    for key,title,description,kind in [('experiments','Experiments','Reproducible counterfactuals. All results currently recorded here are synthetic.','EXPERIMENT'),('field-logs','Field log','Observations kept close to the question that produced them.','FIELD LOG'),('failures','Failure archive','A failure is a record of what the system taught us.','FAILURE')]:
        rendered=[]
        for item in data[key]:
            if key == 'failures':
                body=fields([(label,esc(item[field_name])) for label,field_name in [('SYMPTOM','symptom'),('INITIAL HYPOTHESIS','initialHypothesis'),('ROOT CAUSE','rootCause'),('FIX','fix'),('LESSON','lesson'),('STATUS','status')]])+links(item['evidence'])
            else:
                body=fields([('QUESTION',esc(item['question'])),('OBSERVED',esc(item['observation'])),('HYPOTHESIS',esc(item['hypothesis'])),('NEXT EXPERIMENT',esc(item['nextExperiment']))])+metrics(item.get('measurements',[]))
                if item.get('command'):body+=f'<code class="command">{esc(item["command"])}</code>'
                body+=links([item['source']])
                if item.get('limits'):body+=f'<p class="boundary">{esc(item["limits"])}</p>'
            rendered.append(record(item,kind,body))
        inside='<div class="record-grid">'+''.join(rendered)+'</div>' if rendered else empty('NO RECORDS YET','Entries are added when experiments produce reviewable evidence. An empty archive does not imply that no failures occurred.')
        records.append(f'<section class="subsection evidence-subsection" aria-labelledby="{key}-title"><h3 id="{key}-title">{title}</h3><p>{description}</p>{inside}<p class="empty filter-empty" hidden>No records in this section match the selected system.</p></section>')
    parts.append(section('evidence','03','EVIDENCE / TRACE / FAILURE','Execution leaves a trace.','Source revisions and model limits travel with the results. No benchmark is implied by an animation.',filters+''.join(records)))
    principles='<div class="principles">'+''.join(f'<article class="principle"><h3>{esc(item["name"])}</h3><p>{esc(item["question"])}</p></article>' for item in site['principles'])+'</div>'
    questions='<div class="question-grid">'+''.join(f'<article class="question"><p class="eyebrow">QUESTION / {esc(item["id"])}</p><h3>{esc(item["question"])}</h3><details><summary>Inspect the basis</summary><p>{esc(item["basis"])}</p>{links([item["evidence"]])}</details></article>' for item in data['questions'])+'</div>'
    legend='<div class="depth-legend">'+''.join(f'<div><span class="glyph" aria-hidden="true">{esc(item["symbol"])}</span><span><b>{esc(item["state"])}</b> / {esc(item["meaning"])}</span></div>' for item in data['depth']['legend'])+'</div>'
    depth='<div class="depth-grid">'+''.join(f'<article class="domain"><h4>{esc(item["name"])}</h4><span class="micro">{esc(item["state"])}</span><p>{esc(item["description"])}</p></article>' for item in data['depth']['domains'])+'</div>'
    parts.append(section('questions','04','OPERATING MODEL','Questions I am chasing','Interests become useful when they turn into questions that can survive an experiment.',principles+questions+f'<section class="subsection" aria-labelledby="depth-title"><h3 id="depth-title">Depth map</h3><p>Activity and evidence, never skill percentages. “Built with” describes artifacts, not mastery.</p>{legend}{depth}</section>'))
    categories=list(dict.fromkeys(item['category'] for item in data['tools']))
    tool_filters='<div class="filters" role="group" aria-label="Filter instruments by role">'+''.join(f'<button type="button" data-filter-group="tools" data-filter="{esc(category)}" aria-pressed="{str(category=="all").lower()}">{esc(category.title())}</button>' for category in ['all']+categories)+'</div><p id="tools-count" class="sr-only" aria-live="polite"></p>'
    tools=''.join(f'<details class="tool" data-category="{esc(item["category"])}"><summary><span class="tool-name">{esc(item["name"])}</span><span class="micro">{esc(item["state"])}</span></summary>{fields([("ROLE",esc(item["role"])),("CONNECTED TO",chips(data,item["systems"]) or "Research scope; no implemented connection recorded."),("EVIDENCE BOUNDARY",esc(item.get("note","Its role is described in the linked system records.")))])}</details>' for item in data['tools'])
    parts.append(section('bench','05','THE BENCH','Instrument drawer','Every instrument has a role and a boundary. A tool belongs here because of what it helps expose.',tool_filters+'<div class="tools-grid">'+tools+'</div>'))
    transmissions=''.join(f'<article class="transmission"><p class="eyebrow">TRANSMISSION / {esc(item["id"])} · {esc(item["type"])}</p><h3>{esc(item["title"])}</h3><p>{esc(item["abstract"])}</p><p class="micro">{esc(system_name(data,item["system"]))} / {esc(item["date"] or "DATE NOT DOCUMENTED")}</p>{link(item["source"])}</article>' for item in data['transmissions'])
    parts.append(section('transmissions','06','TRANSMISSIONS','Notes from the machinery.','Existing technical notes, connected to the work that gives them context. No invented publication history.','<div class="transmission-grid">'+transmissions+'</div>' if transmissions else empty('NO TRANSMISSIONS YET','Writing will appear here when it is ready to be inspected.')))
    channel=site['channel']
    channel_body=f'<div class="channel-grid"><div><h3>GOOD REASONS TO OPEN A CHANNEL</h3>{listing(channel["reasons"])}</div><div><h3>A USEFUL FIRST MESSAGE</h3>{listing(channel["protocol"])}</div></div><a class="channel-cta" href="{esc(channel["url"])}">Explore the repositories <span aria-hidden="true">↗</span></a>'
    parts.append(section('channel','07','INTERSECTIONS','Open channel',channel['intro'],channel_body))
    parts.append(f'<footer class="closing"><div class="closing-art" aria-hidden="true">{picture("void-footer.svg",closing=True)}</div><div class="closing-meta"><span>FIELD RECORD / 039<br>CURIOSITY HAS TEETH.</span><a href="https://github.com/rootuser39/RIshabh">Source and research records ↗</a><button class="enhancement" type="button" id="terminal-open">Open Abyss terminal</button></div></footer>')
    return ''.join(parts)


def mdlink(item):
    label=item['label'].replace('[','').replace(']','')
    return f'[{label}]({valid_url(item["url"])})'


def mdpicture(name, alt, width='100%'):
    mobile = name.replace('.svg','-mobile.svg') if name in {'observatory.svg','void-footer.svg'} else None
    parts=['<picture>']
    if mobile:parts.append(f'<source media="(prefers-reduced-motion: reduce) and (max-width: 640px)" srcset="./assets/still/{mobile}" />')
    parts.append(f'<source media="(prefers-reduced-motion: reduce)" srcset="./assets/still/{name}" />')
    if mobile:parts.append(f'<source media="(max-width: 640px)" srcset="./assets/{mobile}" />')
    parts.append(f'<img src="./assets/{name}" width="{width}" alt="{esc(alt)}" /></picture>')
    return '\n'.join(parts)


def render_readme(data, derived):
    site,signal=data['site'],data['current-signal']
    entrance='[Enter the interactive laboratory ↗]('+site['hosting']['url']+')' if site['hosting']['enabled'] else '[Open the interactive laboratory locally](docs/CONTENT.md#run-the-interface) · [Interface source](index.html)'
    parts=[f'<p align="center">\n{mdpicture("observatory.svg","Rishabh D. — the Void Observatory, with the pixel-art Void Dragon and silver event horizon.")}\n</p>', '<p align="center"><a href="#current-signal">Signal</a> &nbsp; / &nbsp; <a href="#systems-in-orbit">Systems</a> &nbsp; / &nbsp; <a href="#evidence">Evidence</a> &nbsp; / &nbsp; <a href="#questions-i-am-chasing">Questions</a> &nbsp; / &nbsp; <a href="#instrument-drawer">Bench</a> &nbsp; / &nbsp; <a href="#open-channel">Channel</a></p>', '# '+site['statement'], "I'm **Rishabh D.** "+site['intro'], '**Architect** the system. **Study** the mechanism. **Make** something worth looking at.', entrance, '<sub>01 / WORKING RECORD</sub>\n\n## Current signal', f'**UPDATED / {signal["updated"]} · {signal["status"]}**\n\n{signal["mode"]}. This is the content edit date, not live telemetry.']
    parts += [f'**{label}**  \n{signal[key]}' for key,label in [('building','BUILDING'),('investigating','INVESTIGATING'),('breaking','BREAKING'),('learning','LEARNING')]]
    latest=next((e for e in data['experiments'] if e['id']==signal.get('latestExperiment')),None)
    if latest:parts.append(f'**LATEST EXPERIMENT**  \n[{latest["id"]} / {latest["title"]}](#experiment--{latest["id"].lower()}) · recorded {latest["date"]} · **{latest["type"]}**')
    parts.append(f'**LAST SHIPPED**  \n[{signal["lastShipped"]["title"]}]({signal["lastShipped"]["url"]}) · {signal["lastShipped"]["date"]}')
    parts.append('**CONTENT TELEMETRY**  \n'+' · '.join(f'{derived["counts"][key]} {label}'+('s' if derived['counts'][key]!=1 else '') for key,label in [('systems','system'),('experiments','experiment'),('fieldLogs','field log'),('failures','failure record'),('transmissions','transmission')])+f'  \nDerived from these content files. Source review / {data["sources"]["reviewed"]}.')
    parts.append('<sub>02 / THE WORK</sub>\n\n## Systems in orbit\n\nInspect the question, the built pieces and the boundary. The records distinguish architecture, prototypes and scaffolding.')
    parts.append('<p align="center">\n'+ '\n'.join(f'<a href="#system--{s["id"]}">{mdpicture(s["asset"],s["name"]+" — "+s["state"],"400")}</a>' for s in data['systems'] if s.get('asset'))+'\n</p>')
    for s in data['systems']:
        body=f'### SYSTEM / {s["id"]}\n\n**{s["name"]} — {s["thesis"]}**\n\n'
        for label,key in [('QUESTION','question'),('WHY IT EXISTS','why'),('CURRENT STATE','state'),('CURRENTLY INVESTIGATING','investigating'),('NEXT EXPERIMENT','nextExperiment')]:body+=f'**{label}**  \n{s[key]}\n\n'
        body+='**ARCHITECTURE**  \n'+' → '.join(s['architecture'])+'\n\n**BUILT**\n\n'+ ('\n'.join('- '+item for item in s['built']) or 'Not yet documented in the public portfolio.')+'\n\n**EVIDENCE**\n\n'+'\n'.join('- '+mdlink(item) for item in s['evidence'])+'\n\n**BOUNDARY**  \n'+s['boundary']
        parts.append(f'<details>\n<summary><b>Inspect {esc(s["name"])}</b> · {esc(s["state"])}</summary>\n\n{body}\n\n</details>')
    parts.append('### System map\n\n'+data['map']['boundary'])
    parts += [f'**{system_name(data,r["from"])} ↔ {system_name(data,r["to"])} / {r["kind"]}**  \n{r["description"]}' for r in data['map']['relationships']]
    parts.append('<details>\n<summary><b>Follow the layers beneath the model</b></summary>\n\n'+'\n\n'.join(f'**{layer["name"]}** — {layer["question"]}  \n'+(' · '.join(system_name(data,i) for i in layer['systems']) or 'No implemented system mapped.') for layer in data['map']['layers'])+'\n\n</details>')
    parts.append('<sub>03 / EVIDENCE</sub>\n\n## Evidence\n\nResults remain attached to a source and an evidence boundary. The congestion results below are synthetic model outputs, not GPU or NIC benchmarks.')
    for key,heading,kind in [('experiments','Experiments','EXPERIMENT'),('field-logs','Field log','FIELD LOG'),('failures','Failure archive','FAILURE')]:
        parts.append('### '+heading)
        for item in data[key]:
            body=f'### {kind} / {item["id"]}\n\n**{item["title"]}**  \n{item.get("date") or "Date not documented"} · '+item.get('type',item.get('status','record'))+'\n\n'
            keys=[('SYMPTOM','symptom'),('INITIAL HYPOTHESIS','initialHypothesis'),('ROOT CAUSE','rootCause'),('FIX','fix'),('LESSON','lesson')] if key=='failures' else [('QUESTION','question'),('OBSERVED','observation'),('HYPOTHESIS','hypothesis'),('NEXT EXPERIMENT','nextExperiment')]
            for label,field_name in keys:body+=f'**{label}**  \n{item[field_name]}\n\n'
            if item.get('measurements'):
                label='MEASURED IN THE SYNTHETIC MODEL' if item.get('type')=='synthetic' else 'MEASURED'
                body+='**'+label+'**\n\n'+'\n'.join(f'- {m["label"]}: '+('not completed' if m['value'] is None else f'{m["value"]} {m["unit"]}') for m in item['measurements'])+'\n\n'
            if item.get('command'):body+='```sh\n'+item['command']+'\n```\n\n'
            evidence=item.get('evidence') or [item['source']]
            body+='**EVIDENCE**\n\n'+'\n'.join('- '+mdlink(source) for source in evidence)
            if item.get('limits'):body+='\n\n**LIMIT**  \n'+item['limits']
            parts.append(f'<details>\n<summary><b>{esc(item["id"])} / {esc(item["title"])}</b></summary>\n\n{body}\n\n</details>')
        if not data[key]:parts.append('No records documented yet. Entries appear when experiments produce reviewable evidence.')
    parts.append('<sub>04 / OPERATING MODEL</sub>\n\n## Operating principles\n\n'+'\n\n'.join(f'**{p["name"]}** — {p["question"]}' for p in site['principles']))
    parts.append('## Questions I am chasing\n\n'+'\n\n'.join(f'**{q["id"]}**  \n{q["question"]}  \n{mdlink(q["evidence"])}' for q in data['questions']))
    parts.append('### Depth map\n\nStates describe documented activity and artifacts, never proficiency percentages.\n\n<details>\n<summary><b>Inspect the exploration states</b></summary>\n\n'+'\n\n'.join(f'**{d["name"]} / {d["state"]}**  \n{d["description"]}' for d in data['depth']['domains'])+'\n\n</details>')
    parts.append('<sub>05 / THE BENCH</sub>\n\n## Instrument drawer\n\nEvery instrument has a role. “Built with” means an artifact exists, not a claim of mastery.\n\n<details>\n<summary><b>Open the drawer</b></summary>\n\n'+'\n\n'.join(f'**{t["name"]} / {t["state"]}**  \n{t["role"]}'+('  \n'+t['note'] if t.get('note') else '') for t in data['tools'])+'\n\n</details>')
    transmissions='\n\n'.join(f'**{t["id"]} / {t["title"]}**  \n{t["abstract"]}  \n{t["date"] or "Date not documented"} · {mdlink(t["source"])}' for t in data['transmissions'])
    parts.append('<sub>06 / TRANSMISSIONS</sub>\n\n## Transmissions\n\n'+(transmissions or 'No transmissions yet. Writing appears here when it is ready to be inspected.'))
    parts.append('<sub>07 / INTERSECTIONS</sub>\n\n## Open channel\n\n'+site['channel']['intro']+'\n\n**GOOD REASONS TO OPEN A CHANNEL**\n\n'+'\n'.join('- '+x for x in site['channel']['reasons'])+'\n\n**A USEFUL FIRST MESSAGE**\n\n'+'\n'.join('- '+x for x in site['channel']['protocol'])+'\n\n[Explore the repositories ↗]('+site['channel']['url']+')')
    parts.append('<p align="center">\n'+mdpicture('void-footer.svg','Curiosity has teeth. Follow the signal. Build what’s underneath.')+'\n</p>')
    parts.append('<p align="center"><sub>FIELD RECORD / 039 · CURIOSITY HAS TEETH.</sub></p>\n\n<!-- Generated from content/*.json by scripts/build_lab.py. Edit content, then rebuild. -->')
    return ('\n\n'.join(parts)+'\n').replace('  \n','<br>\n')


def outputs(data):
    derived={'updated':data['current-signal']['updated'],'sourceReviewed':data['sources']['reviewed'], 'basis':'Content-derived counts, not live activity', 'counts':{key:len(data[name]) for key,name in [('systems','systems'),('experiments','experiments'),('fieldLogs','field-logs'),('failures','failures'),('transmissions','transmissions')]}}
    css=(ROOT/'interface/styles.css').read_text().replace('@@DRAGON_CSS@@',DRAGON_CSS)
    js=(ROOT/'interface/lab.js').read_text()
    digest=lambda value:base64.b64encode(sha256(value.encode()).digest()).decode()
    csp=f"default-src 'none'; img-src 'self' data:; style-src 'sha256-{digest(css)}'; script-src 'sha256-{digest(js)}'; connect-src 'none'; base-uri 'none'; form-action 'none'"
    encoded=json.dumps({**data,'derived':derived},ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    html=(ROOT/'interface/template.html').read_text()
    for placeholder,value in [('CSP',csp),('CSS',css),('BODY',render_body(data,derived)),('DATA',encoded),('JS',js)]:html=html.replace('@@'+placeholder+'@@',value)
    return {'README.md':render_readme(data,derived),'index.html':html,'content/derived.json':json.dumps(derived,indent=2)+'\n', 'assets/omega.svg':'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#090810"/><text x="32" y="45" text-anchor="middle" font-family="serif" font-size="43" fill="#bdacff">Ω</text></svg>\n'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Check generated files without writing.')
    parser.add_argument('--package',type=Path,help='Package a deployable static directory.')
    args=parser.parse_args()
    result=outputs(load_content())
    stale=[]
    for name,value in result.items():
        target=ROOT/name
        if args.check:
            if not target.exists() or target.read_text()!=value:stale.append(name)
        else:
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(value)
    if stale:raise SystemExit('Stale generated files: '+', '.join(stale)+'. Run python scripts/build_lab.py')
    if args.package:
        package=args.package.resolve()
        if package==ROOT or ROOT.is_relative_to(package):raise SystemExit('Choose a separate package directory.')
        package.mkdir(parents=True,exist_ok=True)
        (package/'index.html').write_text(result['index.html'])
        for source in (ROOT/'assets').rglob('*.svg'):
            destination=package/'assets'/source.relative_to(ROOT/'assets')
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,destination)
        for folder in ('docs','tests'):
            for source in (ROOT/folder).rglob('*'):
                if source.is_file() and source.suffix in {'.md','.cjs'}:
                    destination=package/folder/source.relative_to(ROOT/folder)
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(source,destination)
        (package/'.nojekyll').write_text('')
    print('Content valid; README and interface '+('verified.' if args.check else 'generated.'))


if __name__=='__main__':main()
