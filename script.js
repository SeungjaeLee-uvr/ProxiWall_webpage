const demo = document.querySelector(".proximity-demo");
const presence = document.querySelector("#presence");
const distance = document.querySelector("#distance");
const wallPlane = document.querySelector("#wall-plane");
const wallModeTag = document.querySelector("#wall-mode-tag");
const candidateLabel = document.querySelector("#candidate-label");
const candidateCards = document.querySelectorAll(".candidate-card");
const candidateNames = [
  "Gallery Set",
  "Bronze Figure",
  "Celadon Bowl",
  "Moon Jar",
  "White Vessel",
  "Stone Statue",
  "Cube 6",
  "Artifact Detail"
];

function updateWallCandidates(pointerX = 34, pointerY = 50, mode = "OVERVIEW") {
  if (!wallPlane || !wallModeTag || !candidateLabel || !candidateCards.length) return;

  const activeIndex = Math.min(
    candidateCards.length - 1,
    Math.max(0, Math.floor((pointerY / 100) * candidateCards.length))
  );
  const visibleRange = mode === "OVERVIEW" ? 4 : mode === "BROWSING" ? 2 : 1;
  const cardWidth = mode === "OVERVIEW" ? 30 : mode === "BROWSING" ? 44 : 68;
  const cardHeight = mode === "OVERVIEW" ? 38 : mode === "BROWSING" ? 58 : 86;

  wallModeTag.textContent = mode;
  candidateLabel.textContent = `Candidate: ${candidateNames[activeIndex]}`;
  wallPlane.style.setProperty("--focus-x", `${Math.min(86, Math.max(14, pointerX))}%`);
  wallPlane.style.setProperty("--focus-y", `${Math.min(82, Math.max(18, pointerY))}%`);

  candidateCards.forEach((card, index) => {
    const offset = index - activeIndex;
    const visible = Math.abs(offset) <= visibleRange;
    const spread = mode === "OVERVIEW" ? 28 : mode === "BROWSING" ? 48 : 18;
    const scale = index === activeIndex ? 1.22 : mode === "DETAIL" ? .58 : .82;

    card.classList.toggle("is-active", index === activeIndex);
    card.style.setProperty("--card-w", `${cardWidth}px`);
    card.style.setProperty("--card-h", `${cardHeight}px`);
    card.style.setProperty("--candidate-x", "0px");
    card.style.setProperty("--candidate-y", `${offset * spread}px`);
    card.style.setProperty("--candidate-scale", scale);
    card.style.setProperty("--candidate-opacity", visible ? (index === activeIndex ? 1 : .58) : 0);
  });
}

if (demo && presence && distance) {
  updateWallCandidates();

  demo.addEventListener("pointermove", (event) => {
    const bounds = demo.getBoundingClientRect();
    const x = ((event.clientX - bounds.left) / bounds.width) * 100;
    const y = ((event.clientY - bounds.top) / bounds.height) * 100;
    const wallDistance = Math.max(0.08, ((78 - x) / 28) * 2.42);
    const mode = wallDistance > 2 ? "OVERVIEW" : wallDistance > 0.7 ? "BROWSING" : "DETAIL";

    presence.style.left = `${Math.min(72, Math.max(12, x))}%`;
    presence.style.top = `${Math.min(82, Math.max(18, y))}%`;
    distance.textContent = `${wallDistance.toFixed(2)} m · ${mode}`;
    updateWallCandidates(x, y, mode);
  });

  demo.addEventListener("pointerleave", () => {
    presence.style.left = "34%";
    presence.style.top = "50%";
    distance.textContent = "2.42 m · OVERVIEW";
    updateWallCandidates();
  });
}

const youtubeCards = document.querySelectorAll(".youtube-card");
const youtubeModal = document.querySelector("#youtube-modal");
const youtubePlayer = document.querySelector("#youtube-player");
const youtubeModalTitle = document.querySelector("#youtube-modal-title");

function getYouTubeId(url) {
  if (!url) return "";

  try {
    const parsed = new URL(url);
    if (parsed.hostname.includes("youtu.be")) return parsed.pathname.slice(1);
    if (parsed.searchParams.get("v")) return parsed.searchParams.get("v");
    const embedMatch = parsed.pathname.match(/\/(?:embed|shorts)\/([^/?]+)/);
    return embedMatch ? embedMatch[1] : "";
  } catch {
    return "";
  }
}

function closeYouTubeModal() {
  if (!youtubeModal || !youtubePlayer) return;
  youtubeModal.hidden = true;
  youtubePlayer.innerHTML = "";
}

if (youtubeCards.length && youtubeModal && youtubePlayer && youtubeModalTitle) {
  youtubeCards.forEach((card) => {
    const url = card.dataset.youtubeUrl || "";
    const videoId = getYouTubeId(url);
    const thumb = card.querySelector(".youtube-thumb");

    if (!videoId) {
      card.classList.add("is-pending");
      card.setAttribute("aria-disabled", "true");
      return;
    }

    card.classList.remove("is-pending");
    card.removeAttribute("aria-disabled");

    if (thumb) {
      thumb.classList.add("has-image");
      thumb.style.backgroundImage = `url("https://img.youtube.com/vi/${videoId}/hqdefault.jpg")`;
      const label = thumb.querySelector("i");
      if (label) label.textContent = "WATCH DEMO";
    }

    card.addEventListener("click", () => {
      const title = card.dataset.title || "Demo video";
      youtubeModalTitle.textContent = title;
      youtubePlayer.innerHTML = `<iframe src="https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0" title="${title}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>`;
      youtubeModal.hidden = false;
    });
  });

  youtubeModal.querySelectorAll("[data-youtube-close]").forEach((button) => {
    button.addEventListener("click", closeYouTubeModal);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeYouTubeModal();
  });
}
