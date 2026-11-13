document.addEventListener("DOMContentLoaded", function () {
  var button = document.querySelector("[data-app-nav]");
  var side = document.getElementById("app-side");
  if (!button || !side) return;
  button.addEventListener("click", function () {
    var open = side.classList.toggle("is-open");
    button.setAttribute("aria-expanded", open ? "true" : "false");
  });
});
