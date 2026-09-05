document.addEventListener("click", function(e) {
    var btn = e.target.closest(".send-to-estimator");
    if (!btn) return;
    var data = {project_type: btn.dataset.type};
    if (btn.dataset.stitches) {
        data.stitch_count = parseInt(btn.dataset.stitches);
    }
    sessionStorage.setItem("estimator_prefill", JSON.stringify(data));
    window.location.href = "/yarn-estimator/demo.html";
});

document.addEventListener("click", function (e) {
    var btn = e.target.closest("#simulate-hat");
    if (!btn) return;
    var raw = window.hat_sim_instructions;
    var planJson = window.hat_sim_plan;
    if (!raw || !planJson) {
        var err = document.getElementById("demo-error");
        if (err) {
            err.textContent = "Error: Run the Planner first (Plan Crown), then try again.";
            err.style.display = "block";
        }
        return;
    }
    sessionStorage.setItem("knit_sim_instructions", raw);
    sessionStorage.setItem("knit_sim_plan", planJson);
    window.location.href = "/knit-simulator/demo.html";
});
