(function () {
  function passwordIssues(password) {
    var issues = [];
    var value = password || "";
    if (value.length < 12) issues.push("Use at least 12 characters.");
    if (!/[a-z]/.test(value)) issues.push("Add a lowercase letter.");
    if (!/[A-Z]/.test(value)) issues.push("Add an uppercase letter.");
    if (!/\d/.test(value)) issues.push("Add a number.");
    if (!/[^A-Za-z0-9]/.test(value)) issues.push("Add a symbol.");
    return issues;
  }

  function passwordScore(password) {
    var value = password || "";
    var score = 0;
    if (value.length >= 12) score += 1;
    if (/[a-z]/.test(value) && /[A-Z]/.test(value)) score += 1;
    if (/\d/.test(value) && /[^A-Za-z0-9]/.test(value)) score += 1;
    if (value.length >= 16) score += 1;
    return score;
  }

  var labels = ["Too short", "Weak", "Fair", "Strong", "Excellent"];

  function bind(root) {
    root.querySelectorAll("[data-toggle-password]").forEach(function (button) {
      button.addEventListener("click", function () {
        var input = document.getElementById(button.getAttribute("data-toggle-password"));
        if (!input) return;
        var showing = input.type === "text";
        input.type = showing ? "password" : "text";
        button.textContent = showing ? "Show" : "Hide";
        button.setAttribute("aria-pressed", showing ? "false" : "true");
      });
    });

    root.querySelectorAll("[data-password]").forEach(function (input) {
      var form = input.closest("form");
      var meter = form && form.querySelector("[data-strength-meter]");
      var label = form && form.querySelector("[data-strength-label]");
      input.addEventListener("input", function () {
        var score = passwordScore(input.value);
        var issues = passwordIssues(input.value);
        if (meter) meter.setAttribute("data-score", String(score));
        if (label) {
          label.textContent = input.value
            ? labels[score] + (issues.length ? ". " + issues[0] : ".")
            : "Use 12 or more characters with upper and lower case, a number, and a symbol.";
        }
      });
    });

    var username = root.querySelector("[data-username]");
    var hint = root.querySelector("[data-username-hint]");
    if (username && hint) {
      var timer = 0;
      username.addEventListener("input", function () {
        window.clearTimeout(timer);
        timer = window.setTimeout(function () {
          fetch("/api/auth/username-availability/?username=" + encodeURIComponent(username.value))
            .then(function (response) { return response.ok ? response.json() : null; })
            .then(function (data) {
              if (!data) return;
              hint.textContent = data.available ? "Username is available." : "Username is not available.";
            })
            .catch(function () {});
        }, 250);
      });
    }

    root.querySelectorAll("[data-auth-form]").forEach(function (form) {
      form.addEventListener("submit", function () {
        var button = form.querySelector("[data-submit]");
        if (!button || button.disabled) return;
        button.disabled = true;
        button.textContent = "Please wait";
      });
    });
  }

  if (typeof document !== "undefined") {
    document.addEventListener("DOMContentLoaded", function () { bind(document); });
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { passwordIssues: passwordIssues, passwordScore: passwordScore };
  }
})();
