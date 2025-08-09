document.addEventListener("DOMContentLoaded", () => {
  const totalEl = document.getElementById("totalDisplay");
  const inputs = document.querySelectorAll(".menu-item input[type=number]");
  const form = document.querySelector("form");
  const submitBtn = form ? form.querySelector("button[type=submit]") : null;
  let lastTotal = 0;

  // Animate number change
  function animateTotal(newTotal) {
    const duration = 250;
    const start = lastTotal;
    const end = newTotal;
    const startTime = performance.now();

    function animate(time) {
      const progress = Math.min((time - startTime) / duration, 1);
      const value = start + (end - start) * progress;
      totalEl.textContent = `$${value.toFixed(2)}`;
      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        lastTotal = end;
      }
    }
    requestAnimationFrame(animate);
  }

  // Recalculate and update total
  function recalc() {
    let sum = 0;
    inputs.forEach(inp => {
      let qty = parseInt(inp.value, 10) || 0;
      if (qty < 0) qty = 0;
      if (qty > 99) qty = 99; // max limit
      inp.value = qty; // enforce
      const price = parseFloat(inp.closest(".menu-item").dataset.price);
      sum += price * qty;
    });
    animateTotal(sum);

    // Disable submit if total is zero
    if (submitBtn) submitBtn.disabled = sum === 0;
  }

  // Highlight menu item on change
  function highlightChange(e) {
    const card = e.target.closest(".menu-item");
    if (card) {
      card.classList.add("changed");
      setTimeout(() => card.classList.remove("changed"), 400);
    }
  }

  // Reset all inputs and total on form reset
  if (form) {
    form.addEventListener("reset", () => {
      setTimeout(() => {
        recalc();
      }, 50);
    });
  }

  // Attach event listeners to all number inputs
  inputs.forEach(inp => {
    inp.addEventListener("input", recalc);
    inp.addEventListener("change", highlightChange);
  });

  // Initial calculation
  recalc();
});
