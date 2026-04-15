/* ================================================
   DEEPRUN PERFORMANCE CENTER — script.js
   ================================================ */

/* ─── Workout builder (Admin dashboard) ─── */
function addWorkout() {
  const workoutType = document.getElementById('workoutType')?.value;
  const time        = document.getElementById('Time')?.value   || '';
  const weight      = document.getElementById('Weight')?.value || '';
  const reps        = document.getElementById('Reps')?.value   || '';
  const notes       = document.getElementById('Notes')?.value  || '';

  if (!workoutType) return;

  const parts = [`<strong>${workoutType}</strong>`];
  if (time   && time   !== '0') parts.push(`${time} min`);
  if (weight && weight !== '0') parts.push(`${weight} lbs`);
  if (reps   && reps   !== '0') parts.push(`${reps} reps`);
  if (notes  && notes  !== '0') parts.push(`<em>${notes}</em>`);

  const displayText = parts.join(' &middot; ');
  const id          = self.crypto.randomUUID();
  const container   = document.getElementById('addedWorkouts');
  if (!container) return;

  // Display chip
  const item        = document.createElement('div');
  item.className    = 'added-workout-item';
  item.id           = 'display-' + id;
  item.innerHTML    = displayText;
  container.appendChild(item);

  // Build a Python-literal dict string so ast.literal_eval works on the server
  const workoutDict = `{'workoutType': '${workoutType.replace(/'/g,"\\'")}', 'time': '${time.replace(/'/g,"\\'")}', 'weight': '${weight.replace(/'/g,"\\'")}', 'reps': '${reps.replace(/'/g,"\\'")}', 'notes': '${notes.replace(/'/g,"\\'")}'}`;
  const hidden      = document.createElement('input');
  hidden.type       = 'hidden';
  hidden.name       = 'workouts';
  hidden.value      = workoutDict;
  container.appendChild(hidden);

  // Clear inputs
  ['Time','Weight','Reps','Notes'].forEach(f => {
    const el = document.getElementById(f);
    if (el) el.value = '';
  });
  const sel = document.getElementById('workoutType');
  if (sel) sel.selectedIndex = 0;
}

/* ─── Signup: add extra team dropdown ─── */
function addTeamSlot() {
  const container = document.getElementById('teamDropdowns');
  if (!container) return;
  const existing  = container.querySelector('select');
  if (!existing)  return;
  const clone     = existing.cloneNode(true);
  clone.value     = 'none';
  container.appendChild(clone);
}

/* ─── Admin: select-all athletes for a team ─── */
function selectAll(team) {
  document.querySelectorAll('.' + team).forEach(cb => { cb.checked = true; });
}

/* ─── Mark current nav link active ─── */
(function markActive() {
  const path  = window.location.pathname;
  document.querySelectorAll('nav ul li a').forEach(link => {
    const href = link.getAttribute('href');
    if (href && href !== '/' && path.startsWith(href)) {
      link.style.color = 'var(--blue)';
    }
  });
})();

/* ─── Stagger cards on page load ─── */
document.addEventListener('DOMContentLoaded', () => {
  const items = document.querySelectorAll(
    '.stat-card, .workout-card, .request-item, .team-block, .message-bubble'
  );
  items.forEach((el, i) => {
    el.style.opacity   = '0';
    el.style.transform = 'translateY(14px)';
    el.style.transition = `opacity 0.38s ease ${i * 0.06}s, transform 0.38s ease ${i * 0.06}s`;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      el.style.opacity   = '1';
      el.style.transform = 'translateY(0)';
    }));
  });

  // Auto-hide error banners
  const banner = document.querySelector('.error-banner');
  if (banner) {
    setTimeout(() => {
      banner.style.transition = 'opacity 0.6s ease';
      banner.style.opacity    = '0';
      setTimeout(() => banner.remove(), 600);
    }, 4500);
  }
});
