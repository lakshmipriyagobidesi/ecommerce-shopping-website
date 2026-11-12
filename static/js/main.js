document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash").forEach((message) => {
    window.setTimeout(() => {
      message.classList.add("fade-out");
      window.setTimeout(() => message.remove(), 350);
    }, 4500);
  });

  document.querySelectorAll('input[type="number"][name="quantity"]').forEach((input) => {
    input.addEventListener("change", () => {
      const min = Number(input.min || 0);
      const max = Number(input.max || 999);
      let value = Number(input.value);
      if (!Number.isFinite(value)) value = min;
      input.value = Math.min(max, Math.max(min, Math.floor(value)));
    });
  });
});
