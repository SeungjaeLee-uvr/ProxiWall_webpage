const demo = document.querySelector(".proximity-demo");
const presence = document.querySelector("#presence");
const distance = document.querySelector("#distance");

if (demo && presence && distance) {
  demo.addEventListener("pointermove", (event) => {
    const bounds = demo.getBoundingClientRect();
    const x = ((event.clientX - bounds.left) / bounds.width) * 100;
    const y = ((event.clientY - bounds.top) / bounds.height) * 100;
    const wallDistance = Math.max(0.08, ((78 - x) / 28) * 2.42);
    const mode = wallDistance > 2 ? "OVERVIEW" : wallDistance > 0.7 ? "BROWSING" : "DETAIL";

    presence.style.left = `${Math.min(72, Math.max(12, x))}%`;
    presence.style.top = `${Math.min(82, Math.max(18, y))}%`;
    distance.textContent = `${wallDistance.toFixed(2)} m · ${mode}`;
  });

  demo.addEventListener("pointerleave", () => {
    presence.style.left = "34%";
    presence.style.top = "50%";
    distance.textContent = "2.42 m · OVERVIEW";
  });
}
