// Keep links to sections of the original single-page site working.
(() => {
  const destinations = {
    "results": "results.html#results",
    "news": "news.html#news",
    "format": "competition.html#format",
    "awards": "awards.html#awards",
    "timeline": "timeline.html#timeline",
    "leaderboard": "leaderboard.html#leaderboard",
    "registration": "registration.html#registration",
    "dataset": "dataset.html#dataset",
    "verification": "rules.html#verification",
    "organizers": "organizers.html#organizers",
    "contact": "contact.html#contact"
  };
  function redirectLegacySection() {
    const sectionId = window.location.hash.slice(1);
    if (!Object.hasOwn(destinations, sectionId)) return;
    const url = new URL(destinations[sectionId], window.location.href);
    url.search = window.location.search;
    window.location.replace(url.href);
  }
  redirectLegacySection();
  window.addEventListener('hashchange', redirectLegacySection);
})();
