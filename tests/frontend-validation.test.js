const assert = require("assert");
const auth = require("../js/auth.js");

assert.deepStrictEqual(auth.passwordIssues("short"), [
  "Use at least 12 characters.",
  "Add an uppercase letter.",
  "Add a number.",
  "Add a symbol.",
]);
assert.deepStrictEqual(auth.passwordIssues("Correct-Horse-1"), []);
assert.strictEqual(auth.passwordScore(""), 0);
assert.strictEqual(auth.passwordScore("Correct-Horse-1"), 3);
assert.strictEqual(auth.passwordScore("Correct-Horse-12"), 4);
assert.ok(auth.passwordScore("Correct-horse") < 3);

console.log("frontend validation checks passed");
