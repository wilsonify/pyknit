document.addEventListener("click", function(e) {
    var btn = e.target.closest(".send-to-estimator");
    if (!btn) return;
    var data = {stitch_count: parseInt(btn.dataset.stitches), project_type: btn.dataset.type};
    sessionStorage.setItem("estimator_prefill", JSON.stringify(data));
    window.location.href = "/yarn-estimator/demo.html";
});

document.addEventListener("click", function (e) {
    var btn = e.target.closest("#simulate-sock");
    if (!btn) return;
    var raw = window.sock_sim_pattern;
    if (!raw) {
      var err = document.getElementById("demo-error");
      if (err) {
        err.textContent = "Error: Run the Sock Calculator first (or fix your measurements), then try again.";
        err.style.display = "block";
      }
      return;
    }
    var plan = JSON.parse(raw);
    var sel = document.getElementById("sock-size");
    if (sel && sel.selectedOptions && sel.selectedOptions.length) {
      plan.size = sel.selectedOptions[0].textContent;
    }
    sessionStorage.setItem("sock_sim_plan", JSON.stringify(plan));
    window.location.href = "/knit-simulator/demo.html";
});
