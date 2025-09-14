// static/js/main.js
let currentGameId = null;
let busy = false;

function $(id){ return document.getElementById(id); }

async function startNewGame(){
  if(busy) return;
  busy = true;
  const opponent = $('opponent').value;
  const resp = await fetch('/api/new_game', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({opponent})
  });
  const j = await resp.json();
  currentGameId = j.game_id;
  renderState(j.state);
  busy = false;
  await refreshActions();
}

function renderState(state){
  $('state').textContent = JSON.stringify(state, null, 2);
  const ctrl = $('game-controls');
  ctrl.innerHTML = '';

  if(state.game_over){
    const el = document.createElement('div');
    el.textContent = 'Game Over';
    ctrl.appendChild(el);
    return;
  }

  // Always show Roll and Stop buttons for human player
  const rollBtn = document.createElement('button');
  rollBtn.textContent = 'Roll';
  rollBtn.onclick = () => postAction({type:'roll'});
  ctrl.appendChild(rollBtn);

  const stopBtn = document.createElement('button');
  stopBtn.textContent = 'Stop';
  stopBtn.onclick = () => postAction({type:'stop'});
  ctrl.appendChild(stopBtn);
}

async function refreshActions(){
  if(!currentGameId) return;
  const resp = await fetch(`/api/game/${currentGameId}/actions`);
  const j = await resp.json();
  const actions = j.actions || [];
  const container = $('actions');
  container.innerHTML = '';

  if(actions.length === 0){
    container.textContent = 'No actions available (maybe waiting for AI).';
    pollStateUntilHuman();
    return;
  }

  const title = document.createElement('div');
  title.textContent = 'Choose an action:';
  container.appendChild(title);

  actions.forEach((a) => {
    const btn = document.createElement('button');
    btn.textContent = a.label || (typeof a === 'string' ? a : JSON.stringify(a));
    btn.onclick = () => postAction(a);
    container.appendChild(btn);
  });
}

async function postAction(action){
  if(!currentGameId || busy) return;
  busy = true;
  const resp = await fetch(`/api/game/${currentGameId}/action`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({action})
  });
  const j = await resp.json();
  if(j.error){
    alert('Error: ' + j.error);
  } else {
    renderState(j.state);
    await refreshActions();
  }
  busy = false;
}

// Polling helper
let pollHandle = null;
async function pollStateUntilHuman(){
  if(!currentGameId) return;
  if(pollHandle) clearInterval(pollHandle);
  pollHandle = setInterval(async () => {
    const resp = await fetch(`/api/game/${currentGameId}/state`);
    const j = await resp.json();
    renderState(j);
    if((j.available_actions && j.available_actions.length > 0) || j.game_over){
      clearInterval(pollHandle);
      pollHandle = null;
      refreshActions();
    }
  }, 800);
}

window.addEventListener('load', () => {
  $('new-game').addEventListener('click', startNewGame);
});