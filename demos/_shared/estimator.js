document.addEventListener("click", function(e) {
    var btn = e.target.closest(".send-to-estimator");
    if (!btn) return;
    var data = {stitch_count: parseInt(btn.dataset.stitches), project_type: btn.dataset.type};
    sessionStorage.setItem("estimator_prefill", JSON.stringify(data));
    window.location.href = "/yarn-estimator/demo.html";
});
