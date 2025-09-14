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
    }
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
        // Optionally poll the state for AI completion
        pollStateUntilHuman();
        return;
    }
    actions.forEach((a, idx) => {
        const btn = document.createElement('button');
        btn.textContent = typeof a === 'string' ? a : JSON.stringify(a);
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
    // After the server applies human action, it also runs AI turns synchronously
    // so we already have the post-AI state. Refresh available actions.
    await refreshActions();
    }
    busy = false;
}

// Polling helper: poll state until it's the human's turn or game over
let pollHandle = null;
async function pollStateUntilHuman(){
    if(!currentGameId) return;
    if(pollHandle) clearInterval(pollHandle);
    pollHandle = setInterval(async () => {
        const resp = await fetch(`/api/game/${currentGameId}/state`);
        const j = await resp.json();
        renderState(j);
        // If there are available actions, stop polling and render actions
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