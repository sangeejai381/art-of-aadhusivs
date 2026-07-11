document.addEventListener("DOMContentLoaded", () => {
  // ---- Mobile nav toggle ----
  const navToggle = document.getElementById("navToggle");
  const mainNav = document.getElementById("mainNav");
  if (navToggle && mainNav) {
    navToggle.addEventListener("click", () => mainNav.classList.toggle("open"));
  }

  // ---- Admin tabs ----
  const tabBtns = document.querySelectorAll(".tab-btn");
  if (tabBtns.length) {
    tabBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        tabBtns.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        document.querySelectorAll(".tab-panel").forEach((p) => (p.hidden = true));
        const target = document.getElementById("tab-" + btn.dataset.tab);
        if (target) target.hidden = false;
      });
    });
  }

  // ---- Admin inline edit toggles ----
  document.querySelectorAll(".js-edit-toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      const panel = document.getElementById(btn.dataset.target);
      if (panel) panel.hidden = !panel.hidden;
    });
  });

  // ---- Inquiry modal ----
  const overlay = document.getElementById("inquiryOverlay");
  const closeBtn = document.getElementById("inquiryClose");
  const form = document.getElementById("inquiryForm");
  const productIdField = document.getElementById("inquiryProductId");
  const productLine = document.getElementById("inquiryProductLine");
  const successBox = document.getElementById("inquirySuccess");

  function openModal(productId, productName) {
    if (!overlay) return;
    productIdField.value = productId || "";
    productLine.textContent = productName
      ? `About: ${productName}`
      : "Tell us how to reach you and we'll follow up.";
    form.hidden = false;
    successBox.hidden = true;
    overlay.classList.add("open");
  }
  function closeModal() {
    overlay.classList.remove("open");
  }

  document.querySelectorAll(".js-inquire").forEach((btn) => {
    btn.addEventListener("click", () => {
      openModal(btn.dataset.productId, btn.dataset.productName);
    });
  });
  if (closeBtn) closeBtn.addEventListener("click", closeModal);
  if (overlay) {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) closeModal();
    });
  }

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const data = new FormData(form);
      try {
        const res = await fetch("/inquire", { method: "POST", body: data });
        const json = await res.json();
        if (json.ok) {
          form.hidden = true;
          successBox.hidden = false;
          form.reset();
        } else {
          alert(json.error || "Something went wrong, please try again.");
        }
      } catch (err) {
        alert("Network error — please try again or DM us directly.");
      }
    });
  }
});
