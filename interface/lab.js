(() => {
  'use strict';
  const content = JSON.parse(document.getElementById('lab-content').textContent);
  const root = document.documentElement;
  const pet = document.querySelector('.pet');
  const petState = document.getElementById('pet-state');
  const motionButton = document.getElementById('motion-toggle');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const dialog = document.getElementById('abyss-terminal');
  const command = document.getElementById('terminal-command');
  const output = document.getElementById('terminal-output');
  let inactivityTimer;
  let reactionTimer;
  let lastDialogTrigger;
  let paused = false;
  let omegaCount = 0;
  let omegaReset;
  try { paused = localStorage.getItem('void-observatory-motion') === 'paused'; } catch {}

  function state(value, duration = 0) {
    if(window.VoidLab) { window.VoidLab.react(value,duration); return; }
    clearTimeout(reactionTimer);
    pet.dataset.state = value;
    petState.textContent = value.toUpperCase();
    if (duration) reactionTimer = setTimeout(() => state('idle'), duration);
  }
  function resetInactivity() {
    if(window.VoidLab) { window.VoidLab.resetIdle(); return; }
    clearTimeout(inactivityTimer);
    if (pet.dataset.state === 'sleeping') state('idle');
    if (!document.hidden) inactivityTimer = setTimeout(() => state('sleeping'), 90000);
  }
  function updateMotion() {
    const stopped = paused || reduced.matches;
    root.classList.toggle('motion-off', stopped);
    for(const button of document.querySelectorAll('#motion-toggle,.motion-short')) {
      button.setAttribute('aria-pressed',String(stopped));
      button.textContent=reduced.matches?'Motion reduced':paused?'Resume motion':'Pause motion';
      button.disabled=reduced.matches;
    }
    window.VoidLab?.setMotion(stopped);
    for (const source of document.querySelectorAll('source[data-motion-media]')) {
      const original = source.dataset.motionMedia;
      source.media = paused ? original.replace('(prefers-reduced-motion: reduce) and ', '').replace('(prefers-reduced-motion: reduce)', 'all') : original;
    }
  }
  for(const button of document.querySelectorAll('#motion-toggle,.motion-short')) button.addEventListener('click', () => {
    paused = !paused;
    try { localStorage.setItem('void-observatory-motion', paused ? 'paused' : 'running'); } catch {}
    updateMotion();
  });
  reduced.addEventListener('change', updateMotion);
  document.getElementById('pet-observe').addEventListener('click', () => state('observing', 2500));
  for (const detail of document.querySelectorAll('details')) {
    detail.addEventListener('toggle', () => {
      if (detail.open && !detail.classList.contains('system') && !detail.classList.contains('record')) state(detail.classList.contains('failure') ? 'alert' : detail.classList.contains('experiment') ? 'working' : 'observing', 2500);
    });
  }
  document.addEventListener('pointerdown', resetInactivity, {passive:true});
  document.addEventListener('keydown', resetInactivity);
  document.addEventListener('visibilitychange', () => {
    if(window.VoidLab) return;
    root.classList.toggle('page-away', document.hidden);
    if(document.hidden) { clearTimeout(inactivityTimer); state('sleeping'); }
    else { state('idle'); resetInactivity(); }
  });

  function filter(group, attribute, records, countId) {
    for (const button of document.querySelectorAll(`[data-filter-group="${group}"]`)) {
      button.addEventListener('click', () => {
        const value = button.dataset.filter;
        for (const peer of document.querySelectorAll(`[data-filter-group="${group}"]`)) peer.setAttribute('aria-pressed', String(peer === button));
        let visible = 0;
        for (const record of document.querySelectorAll(records)) {
          record.hidden = value !== 'all' && record.dataset[attribute] !== value;
          if (!record.hidden) visible++;
        }
        if (countId) document.getElementById(countId).textContent = `${visible} record${visible === 1 ? '' : 's'} shown.`;
        if (group === 'evidence') {
          for (const section of document.querySelectorAll('.evidence-subsection')) {
            const any = Array.from(section.querySelectorAll('.record')).some(record => !record.hidden);
            section.querySelector('.filter-empty').hidden = any;
          }
        }
      });
    }
  }
  filter('evidence', 'system', '#evidence .record', 'evidence-count');
  filter('tools', 'category', '.tool', 'tools-count');

  for (const button of document.querySelectorAll('[data-layer]')) {
    button.addEventListener('click', () => {
      const layer = content.map.layers.find(layer => layer.id === button.dataset.layer);
      const selected = button.getAttribute('aria-pressed') !== 'true';
      for (const peer of document.querySelectorAll('[data-layer]')) peer.setAttribute('aria-pressed', String(selected && peer === button));
      for (const system of document.querySelectorAll('.system')) system.classList.toggle('context-active', selected && layer.systems.includes(system.dataset.system));
      const names = layer.systems.map(id => content.systems.find(system => system.id === id).name);
      document.getElementById('layer-note').textContent = selected ? `${layer.name}: ${names.length ? names.join(' · ') : 'no implemented system is mapped here'}. Scope is described in each system’s evidence boundary.` : content.map.boundary;
      state('observing', 2000);
    });
  }

  function openTerminal(trigger) {
    if (dialog.open) return;
    lastDialogTrigger = trigger;
    dialog.showModal();
    window.VoidLab?.terminal(true);
    command.focus();
  }
  function closeTerminal() {
    dialog.close();
    window.VoidLab?.terminal(false);
    if(lastDialogTrigger) lastDialogTrigger.focus();
  }
  for (const trigger of document.querySelectorAll('.omega-trigger')) {
    trigger.addEventListener('click', () => {
      clearTimeout(omegaReset);
      omegaCount++;
      omegaReset = setTimeout(() => { omegaCount = 0; }, 7000);
      if (omegaCount >= 5) { omegaCount = 0; openTerminal(trigger); }
    });
  }
  document.getElementById('terminal-open').addEventListener('click', event => openTerminal(event.currentTarget));
  document.getElementById('terminal-close').addEventListener('click', closeTerminal);
  dialog.addEventListener('cancel', () => { window.VoidLab?.terminal(false); if(lastDialogTrigger) lastDialogTrigger.focus(); });
  const commands = {
    help: () => 'systems / experiments / failures / signal / dragon / whoami / clear',
    systems: () => content.systems.map(system => `${system.name}: ${system.state}`).join('\n'),
    experiments: () => content.experiments.map(experiment => `${experiment.id}: ${experiment.title} [${experiment.type}]`).join('\n') || 'No experiments documented.',
    failures: () => content.failures.map(failure => `${failure.id}: ${failure.title} [${failure.status}]`).join('\n') || 'No failures documented.',
    signal: () => `updated: ${content['current-signal'].updated}\nmode: ${content['current-signal'].mode}\n${content['current-signal'].building}`,
    dragon: () => { window.VoidLab?.dragonCommand(); return 'VOID DRAGON / 01\nstate: observing\npurpose: curiosity\nThis is an interface companion, not telemetry.'; },
    whoami: () => `${content.site.name}\n${content.site.statement}\nFIELD RECORD / 039`,
  };
  document.getElementById('terminal-form').addEventListener('submit', event => {
    event.preventDefault();
    const raw = command.value.trim();
    const key = raw.toLowerCase();
    command.value = '';
    if (!raw) return;
    if (key === 'clear') { output.textContent = 'FIELD RECORD / 039'; return; }
    const result = Object.hasOwn(commands, key) ? commands[key]() : 'Unknown command. Type help.';
    // User text is always text, never HTML or executable code.
    output.textContent = `${output.textContent}\n\n> ${raw}\n${result}`.split('\n').slice(-180).join('\n');
    output.scrollTop = output.scrollHeight;
  });

  if ('IntersectionObserver' in window) {
    const nav = document.querySelector('nav[aria-label="Laboratory navigation"]');
    const observer = new IntersectionObserver(entries => {
      const entering = entries.filter(entry => entry.isIntersecting).sort((a,b) => b.intersectionRatio-a.intersectionRatio)[0];
      if (!entering) return;
      for (const link of nav.querySelectorAll('a')) {
        if(link.hash === `#${entering.target.id}`) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      }
    }, {rootMargin:'-10% 0px -65% 0px',threshold:0});
    for (const section of document.querySelectorAll('section[id]')) observer.observe(section);
  }
  updateMotion();
  resetInactivity();
  root.classList.add('enhanced');
})();
