// IMPORTANT: replace this URL with the Apps Script Web App URL after deployment
const REG_ENDPOINT = 'https://script.google.com/macros/s/AKfycbzTizIX8modAv6T2L6J9Klvp7wXjk7gkU8Pxi0jlQMER0LXlwxqoSDLhh1AUpRGW7pitg/exec';
// Hong Kong relay (Tencent SCF) — reachable from mainland China where Google is blocked.
// It forwards the same payload to the Apps Script above, so entries land in the SAME sheet.
const REG_RELAY = 'https://1448216525-1thwxjsvcn.ap-hongkong.tencentscf.com';

const regModal = document.getElementById('reg-modal');
const regOpen = document.getElementById('prereg-open');
const regClose = document.getElementById('reg-modal-close');
const regForm = document.getElementById('reg-form');
const regSubmit = document.getElementById('reg-submit');
const regStatus = document.getElementById('reg-status');

function openRegModal() {
  regModal.classList.add('open');
  document.body.classList.add('modal-open');
  regStatus.textContent = '';
  regStatus.className = 'form-status';
}
function closeRegModal() {
  regModal.classList.remove('open');
  document.body.classList.remove('modal-open');
}

regOpen?.addEventListener('click', openRegModal);
regClose?.addEventListener('click', closeRegModal);
regModal?.addEventListener('click', (e) => { if (e.target === regModal) closeRegModal(); });
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && regModal.classList.contains('open')) closeRegModal(); });

// Dynamic team-member inputs (max 3)
const MAX_MEMBERS = 3;
const membersList = document.getElementById('members-list');
const addMemberBtn = document.getElementById('add-member-btn');

function updateAddMemberBtn() {
  const count = membersList.querySelectorAll('.member-input').length;
  if (count >= MAX_MEMBERS) {
    addMemberBtn.disabled = true;
    addMemberBtn.textContent = `+ Add team member (max ${MAX_MEMBERS} reached)`;
  } else {
    addMemberBtn.disabled = false;
    addMemberBtn.textContent = '+ Add team member';
  }
}

addMemberBtn?.addEventListener('click', () => {
  const count = membersList.querySelectorAll('.member-input').length;
  if (count >= MAX_MEMBERS) return;
  const div = document.createElement('div');
  div.className = 'member-input';
  div.innerHTML = `<input type="text" name="member" placeholder="Member ${count + 1}" maxlength="80"/>
    <button type="button" class="remove-member-btn" aria-label="Remove member">×</button>`;
  membersList.appendChild(div);
  div.querySelector('.remove-member-btn').addEventListener('click', () => {
    div.remove();
    updateAddMemberBtn();
  });
  updateAddMemberBtn();
});

regForm?.addEventListener('submit', async (e) => {
  e.preventDefault();

  // Build payload
  const fd = new FormData(regForm);
  const tracks = [];
  if (fd.get('track_small')) tracks.push('Small');
  if (fd.get('track_large')) tracks.push('Large');
  if (tracks.length === 0) {
    regStatus.textContent = '⚠ Please select at least one track.';
    regStatus.className = 'form-status error';
    return;
  }

  // Collect all team member names from dynamic inputs
  const memberInputs = regForm.querySelectorAll('input[name="member"]');
  const members = Array.from(memberInputs).map(i => i.value.trim()).filter(v => v);
  if (members.length === 0) {
    regStatus.textContent = '⚠ Please add at least one team member.';
    regStatus.className = 'form-status error';
    return;
  }

  const payload = {
    team_name: fd.get('team_name') || '',
    leader_email: fd.get('leader_email') || '',
    affiliation: fd.get('affiliation') || '',
    country: fd.get('country') || '',
    tracks: tracks,
    members: members,
    advisor: fd.get('advisor') || '',
    submitted_at: new Date().toISOString()
  };

  regSubmit.disabled = true;
  regStatus.textContent = 'Submitting…';
  regStatus.className = 'form-status loading';

  const CONTACT = 'cuhkx.competition@gmail.com';
  const SUCCESS_MSG = '✓ Registration confirmed — your team has been saved to our records. Organizers will be in touch via the contact email you provided.';
  // Reason first, then this shared line directing the team to email us.
  const MANUAL = ' Please email us at ' + CONTACT + ' and we will register your team manually.';

  try {
    // Submit via the Hong Kong relay. It forwards to the Google Apps Script,
    // reads the REAL result, and returns { ok: true } ONLY after the row is
    // actually written to the sheet — so success here is genuinely confirmed.
    // The relay is reachable both worldwide and from mainland China.
    const relayRes = await fetch(REG_RELAY, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify(payload)
    });
    const data = await relayRes.json().catch(() => ({}));

    if (relayRes.ok && data.ok === true) {
      // Confirmed: the row was written to the Google Sheet.
      // Keep the submitted values on screen (do NOT reset the form) so the
      // team can review what they sent.
      regStatus.textContent = SUCCESS_MSG;
      regStatus.className = 'form-status success';
    } else {
      // Reached the server, but the sheet write was NOT confirmed.
      regStatus.textContent = '✗ We received your request but could not save it to our records.' + MANUAL;
      regStatus.className = 'form-status error';
    }
  } catch (err) {
    // The relay was unreachable. Best-effort: also post directly to Google so
    // the data may still arrive — but we cannot confirm, so show a failure
    // message and let the team email us for a manual registration.
    try {
      await fetch(REG_ENDPOINT, {
        method: 'POST',
        mode: 'no-cors',
        headers: { 'Content-Type': 'text/plain;charset=utf-8' },
        body: JSON.stringify(payload)
      });
    } catch (err2) { /* ignore — nothing more we can do from the browser */ }
    regStatus.textContent = '✗ Submission failed — your network may be blocking it. Try another network or a VPN.' + MANUAL;
    regStatus.className = 'form-status error';
  } finally {
    regSubmit.disabled = false;
  }
});
