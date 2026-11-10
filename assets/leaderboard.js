let LB_DATA = null;
let CURRENT_TRACK = 'small';

async function loadLeaderboard() {
  try {
    const res = await fetch('leaderboard.json?_=' + Date.now());
    if (!res.ok) throw new Error('not found');
    LB_DATA = await res.json();
    if (LB_DATA.updated_at) {
      const d = new Date(LB_DATA.updated_at);
      const opts = { timeZone: 'UTC', year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false };
      document.getElementById('lb-updated').textContent = 'Last updated: ' + d.toLocaleString('en-US', opts) + ' UTC';
    }
  } catch (e) {
    LB_DATA = null;
  }
  renderLeaderboard(CURRENT_TRACK);
}

function renderLeaderboard(track) {
  CURRENT_TRACK = track;
  const body = document.getElementById('lb-body');
  const sourceLink = document.getElementById('lb-source-link');

  const trackData = LB_DATA && LB_DATA[track];
  if (trackData && trackData.kaggle_url) {
    sourceLink.href = trackData.kaggle_url;
  }

  const teamCountEl = document.getElementById('lb-teamcount');
  if (teamCountEl) {
    const tc = trackData && (trackData.team_count ?? trackData.teamCount);
    const label = track === 'small' ? 'Small Model Track' : 'Large Model Track';
    teamCountEl.innerHTML = (typeof tc === 'number' && tc >= 0)
      ? `<strong>${tc}</strong> teams recorded in the ${label}`
      : '';
  }

  if (!trackData || !trackData.entries || trackData.entries.length === 0) {
    body.innerHTML = '<tr><td colspan="4" class="lb-empty"><strong>Public snapshot unavailable</strong>The saved public leaderboard could not be loaded. Please try again later; private results are not published here.</td></tr>';
    return;
  }

  body.innerHTML = trackData.entries.slice(0, 6).map((e, i) => {
    const rank = e.rank || (i + 1);
    let rcClass = 'n';
    if (rank === 1) rcClass = 'g';
    else if (rank === 2) rcClass = 's';
    else if (rank === 3) rcClass = 'b';
    const rowClass = rank <= 3 ? `r${rank}` : '';
    return `<tr class="${rowClass}">
      <td><span class="rc ${rcClass}">${rank}</span></td>
      <td class="lb-team">${escapeHtml(e.team)}</td>
      <td class="lb-score">${escapeHtml(String(e.score))}</td>
      <td class="lb-date">${escapeHtml(e.last_submission || '—')}</td>
    </tr>`;
  }).join('');
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]);
}

document.querySelectorAll('.lb-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.lb-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    renderLeaderboard(tab.dataset.track);
  });
});

loadLeaderboard();
