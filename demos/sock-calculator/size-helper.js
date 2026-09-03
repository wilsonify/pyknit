document.addEventListener("DOMContentLoaded", function () {
  var sel = document.getElementById("sock-size");
  if (!sel) return;
  sel.addEventListener("change", function () {
    var o = sel.options[sel.selectedIndex];
    if (!o || !o.dataset.top) return;
    document.getElementById("circumference_at_top").value = o.dataset.top;
    document.getElementById("circumference_of_ankle").value = o.dataset.ankle;
    document.getElementById("length_from_sock_top_to_heel_bottom").value = o.dataset.leg;
    document.getElementById("length_from_heel_to_toe").value = o.dataset.foot;
  });
});
