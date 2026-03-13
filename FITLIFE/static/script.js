// FitLife small UI interactions: reveal-on-scroll + fancy role selection

function revealOnScroll() {
  document.querySelectorAll(".reveal").forEach(el => {
    const top = el.getBoundingClientRect().top;
    if (top < window.innerHeight - 80) el.classList.add("show");
  });
}
window.addEventListener("scroll", revealOnScroll);
window.addEventListener("load", revealOnScroll);
revealOnScroll();

// role card selection styling
function wireRoleCards() {
  const cards = document.querySelectorAll(".role-card");
  if (!cards.length) return;

  function sync() {
    cards.forEach(card => {
      const radio = card.querySelector("input[type='radio']");
      card.dataset.selected = radio && radio.checked ? "true" : "false";
    });
  }

  cards.forEach(card => {
    card.addEventListener("click", () => {
      const radio = card.querySelector("input[type='radio']");
      if (radio) radio.checked = true;
      sync();
    });
    const radio = card.querySelector("input[type='radio']");
    if (radio) radio.addEventListener("change", sync);
  });

  sync();
}
window.addEventListener("load", wireRoleCards);
