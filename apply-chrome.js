const fs = require("fs");
const path = require("path");

const root = __dirname;
const header = fs.readFileSync(path.join(root, "partials", "header.html"), "utf8").trim();
const footer = fs.readFileSync(path.join(root, "partials", "footer.html"), "utf8").trim();

const head = `  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TITLE</title>
  <meta name="description" content="DESC">
  <meta name="theme-color" content="#050807">
  <link rel="icon" href="assets/favicon-mark.png" type="image/png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/site.css">`;

function page(filename, title, description, body) {
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
${head.replace("TITLE", title).replace("DESC", description)}
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <!-- chrome:header -->
  <!-- /chrome:header -->
  <main id="main">
${body}
  </main>
  <!-- chrome:footer -->
  <!-- /chrome:footer -->
  <script src="js/site.js"></script>
</body>
</html>
`;
  fs.writeFileSync(path.join(root, filename), html);
}

page(
  "login.html",
  "Log in · ZeroTrace Academy",
  "Sign-in for ZeroTrace Academy. Accounts are not open on this preview, and this form does not create a session.",
  `    <div class="wrap page-hero">
      <p class="kicker">Account · not open</p>
      <h1>Log in</h1>
      <p class="lede">Accounts are not open while the academy is being built. Submitting this form does not sign you in.</p>
      <form class="stack-form" action="login.html#account-status" method="get">
        <label>Email
          <input class="field" type="email" autocomplete="username" required>
        </label>
        <label>Password
          <input class="field" type="password" autocomplete="current-password" required>
        </label>
        <button class="btn btn-signal" type="submit">Log in</button>
      </form>
      <div class="status" id="account-status">
        <p>No session is created. The password field has no name, so the browser does not put it in the page address or send it to a server.</p>
      </div>
      <p class="note">New here? <a class="text-link" href="register.html">Get started</a></p>
    </div>`
);

page(
  "register.html",
  "Get started · ZeroTrace Academy",
  "Registration for ZeroTrace Academy. Enrolment is not open, and this form does not create an account.",
  `    <div class="wrap page-hero">
      <p class="kicker">Enrolment · not open</p>
      <h1>Get started</h1>
      <p class="lede">Joining ZeroTrace will open with the academy. This form does not create an account, start a plan, or store what you type.</p>
      <form class="stack-form" action="register.html#account-status" method="get">
        <label>Name
          <input class="field" type="text" autocomplete="name" required>
        </label>
        <label>Email
          <input class="field" type="email" autocomplete="email" required>
        </label>
        <label>Password
          <input class="field" type="password" autocomplete="new-password" required>
        </label>
        <button class="btn btn-signal" type="submit">Create account</button>
      </form>
      <div class="status" id="account-status">
        <p>No account is created. Password fields on this preview are unnamed, so they are not submitted. Proposed plans are listed on the pricing page and are not for sale yet.</p>
      </div>
      <p class="note">Already registered later? <a class="text-link" href="login.html">Log in</a> · <a class="text-link" href="pricing.html">View proposed plans</a></p>
    </div>`
);

page(
  "research.html",
  "Research · ZeroTrace Academy",
  "The ZeroTrace research library. No papers are listed yet. The AI mentor on this site is a preview with no model connected.",
  `    <div class="wrap page-hero">
      <p class="kicker">Research library</p>
      <h1>Nothing published yet.</h1>
      <p class="lede">Articles, lab write-ups, and research notes will be listed here when they exist. This page does not invent papers, authors, or citation counts.</p>
    </div>
    <section class="section" style="padding-top:0">
      <div class="wrap edit-grid">
        <article class="edit-card"><span class="tag">Empty</span><h3>Research publications</h3><p>No papers are in the library.</p></article>
        <article class="edit-card"><span class="tag">Planned</span><h3>Security write-ups</h3><p>Challenge and lab notes will be added after the range exists, and only for authorised exercises.</p></article>
        <article class="edit-card"><span class="tag">Planned</span><h3>CTF competitions</h3><p>Events will be announced when a date and an isolated environment exist. <a class="text-link" href="range.html#ctf">CTF arena</a></p></article>
        <article class="edit-card" id="mentor"><span class="tag tag-warn">Preview</span><h3>AI learning</h3><p>The mentor on the homepage is a layout. No model is connected, and questions are not sent anywhere. <a class="text-link" href="index.html#mentor">Open the preview</a></p></article>
      </div>
    </section>`
);

page(
  "about.html",
  "About · ZeroTrace Academy",
  "ZeroTrace Academy is a pre-launch cybersecurity learning, tools, and simulation ecosystem.",
  `    <div class="wrap page-hero">
      <p class="kicker">About</p>
      <h1>From learner to cybersecurity professional.</h1>
      <p class="lede">ZeroTrace Academy is being built as one ecosystem: structured learning, a private cyber range, original security tools, and room for research. It is not a generic course list, and it is not open for enrolment yet.</p>
      <p class="lede" style="margin-top:1rem">Practical offensive work stays inside isolated systems a learner owns or is explicitly allowed to test. The public website does not run lab machines.</p>
      <p class="note">The catalog currently describes 31 departments, 6 learning paths, 6 lab categories in development, and 24 proposed tools.</p>
    </div>`
);

page(
  "contact.html",
  "Contact · ZeroTrace Academy",
  "Contact ZeroTrace Academy. A public address has not been verified yet, and this form does not send a message.",
  `    <div class="wrap page-hero">
      <p class="kicker">Contact</p>
      <h1>A verified address is not published yet.</h1>
      <p class="lede">Until a contact channel is confirmed, this form does not deliver a message. Do not include secrets, credentials, or vulnerability details.</p>
      <form class="stack-form" action="contact.html#sent" method="get">
        <label>Name
          <input class="field" type="text" autocomplete="name">
        </label>
        <label>Email
          <input class="field" type="email" autocomplete="email">
        </label>
        <label>Message
          <textarea class="field" rows="5"></textarea>
        </label>
        <button class="btn btn-signal" type="submit">Send</button>
      </form>
      <div class="status" id="sent">
        <p>Nothing was sent. Fields on this form have no names, so the browser does not submit their contents.</p>
      </div>
    </div>`
);

page(
  "careers.html",
  "Careers · ZeroTrace Academy",
  "Careers at ZeroTrace Academy. No open roles are listed.",
  `    <div class="wrap page-hero">
      <p class="kicker">Careers</p>
      <h1>No open roles are listed.</h1>
      <p class="lede">When ZeroTrace hires, roles will be posted here. This page does not advertise jobs that do not exist.</p>
      <p class="note"><a class="text-link" href="contact.html">Contact</a> will accept applications after a verified address is published.</p>
    </div>`
);

page(
  "blog.html",
  "Blog · ZeroTrace Academy",
  "The ZeroTrace Academy blog. No articles are published yet.",
  `    <div class="wrap page-hero">
      <p class="kicker">Blog</p>
      <h1>No articles yet.</h1>
      <p class="lede">Technical notes will appear here when they are written. There is no archive to browse.</p>
    </div>`
);

page(
  "tutorials.html",
  "Tutorials · ZeroTrace Academy",
  "ZeroTrace Academy tutorials. Lessons will be added as the curriculum is written.",
  `    <div class="wrap page-hero">
      <p class="kicker">Tutorials</p>
      <h1>Lessons are still being written.</h1>
      <p class="lede">Tutorials will follow the catalog, starting with foundations. Nothing here is a live class.</p>
      <p class="note"><a class="text-link" href="catalog.html">Browse the 31 departments</a></p>
    </div>`
);

page(
  "docs.html",
  "Documentation · ZeroTrace Academy",
  "ZeroTrace Academy documentation. Product docs will ship with each release.",
  `    <div class="wrap page-hero">
      <p class="kicker">Documentation</p>
      <h1>Docs follow the releases.</h1>
      <p class="lede">Tool and range documentation will be published when those products exist. The proposed toolkit is described on the tools page, and none of it is available to run.</p>
      <p class="note"><a class="text-link" href="tools.html">Proposed tools</a> · <a class="text-link" href="range.html">Range preview</a></p>
    </div>`
);

page(
  "community.html",
  "Community · ZeroTrace Academy",
  "The ZeroTrace community space is not open. No member count is shown.",
  `    <div class="wrap page-hero">
      <p class="kicker">Community</p>
      <h1>The room is not open.</h1>
      <p class="lede">Discussions, study groups, and project showcases will live here later. No member count is shown because there is no community to count.</p>
      <p class="note">Competitions, when scheduled, will use isolated labs. <a class="text-link" href="legal.html#disclosure">Responsible disclosure</a></p>
    </div>`
);

page(
  "legal.html",
  "Legal · ZeroTrace Academy",
  "Draft privacy, terms, acceptable use, responsible disclosure, and cookie notes for the ZeroTrace Academy preview site.",
  `    <div class="wrap page-hero">
      <p class="kicker">Legal · draft</p>
      <h1>Policies for a site that is not launched.</h1>
      <p class="lede">These are plain-language drafts for the preview. They are not a substitute for legal advice and will be replaced before enrolment or payment opens.</p>
    </div>
    <div class="wrap legal-copy">
      <section id="privacy">
        <h2>Privacy policy</h2>
        <p>This preview does not run accounts, payments, or analytics. Forms on the login, registration, and contact pages do not submit field values, because those fields have no names.</p>
        <p>When accounts exist, the privacy notice will name the data collected, why it is kept, and how to ask for it. Do not send secrets to this site.</p>
      </section>
      <section id="terms">
        <h2>Terms and conditions</h2>
        <p>The pages describe a product in development. Catalogues, prices, lab access, and tool lists can change. Nothing on the site is an offer to sell a subscription.</p>
        <p>Completion records, if they are added later, are not accredited professional certifications.</p>
      </section>
      <section id="aup">
        <h2>Acceptable use policy</h2>
        <p>Security practice belongs on systems you own or are explicitly authorised to test. Do not use ZeroTrace material against third-party systems. Do not attempt to break this website, other learners, or any service that has not been provided as a lab.</p>
        <p>Lab machines, when they exist, will be isolated. They will not run on the public website server, and they will not be unlimited.</p>
      </section>
      <section id="disclosure">
        <h2>Responsible disclosure</h2>
        <p>If you find a problem with this website, wait for a verified contact address before sending details. Do not include exploit steps in a public issue. There is no bug-bounty programme announced.</p>
        <p>Testing the academy’s own marketing site without permission is not invited. Authorised testing will be scoped in writing when a channel exists.</p>
      </section>
      <section id="cookies">
        <h2>Cookie policy</h2>
        <p>This preview does not set tracking cookies and does not load advertising scripts. A font stylesheet is requested from Google Fonts. If that changes, this note will change with it.</p>
      </section>
    </div>`
);

function stamp(html) {
  if (html.includes("<!-- chrome:header -->")) {
    html = html.replace(
      /<!-- chrome:header -->[\s\S]*?<!-- \/chrome:header -->/,
      `<!-- chrome:header -->\n  ${header}\n  <!-- /chrome:header -->`
    );
    html = html.replace(
      /<!-- chrome:footer -->[\s\S]*?<!-- \/chrome:footer -->/,
      `<!-- chrome:footer -->\n  ${footer}\n  <!-- /chrome:footer -->`
    );
  } else {
    html = html.replace(/<header class="site-header"[\s\S]*?<\/header>/, header);
    html = html.replace(/<footer class="site-footer"[\s\S]*?<\/footer>/, footer);
  }
  html = html.replace(
    /<meta name="theme-color" content="[^"]*">/,
    '<meta name="theme-color" content="#050807">'
  );
  html = html.replace(
    /<link href="https:\/\/fonts\.googleapis\.com\/css2\?family=Fraunces[^"]+"/,
    '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap"'
  );
  html = html.replace(
    /<link rel="icon" href="favicon.svg" type="image\/svg\+xml">/,
    '<link rel="icon" href="assets/favicon-mark.png" type="image/png">'
  );
  return html;
}

const catalogIds = {
  "CS &amp; IT Fundamentals": "cs-it-fundamentals",
  Networking: "networking",
  "Linux Security": "linux-security",
  "Windows Security": "windows-security",
  "Programming &amp; Scripting": "programming-scripting",
  Cryptography: "cryptography",
  "Ethical Hacking": "ethical-hacking",
  "Web Application Security": "web-application-security",
  "API Security": "api-security",
  "Network Penetration Testing": "network-penetration-testing",
  "Wireless Security": "wireless-security",
  "Active Directory Security": "active-directory-security",
  "Red Team Operations": "red-team-operations",
  "Blue Team Operations": "blue-team-operations",
  "Purple Team Operations": "purple-team-operations",
  "SOC Operations": "soc-operations",
  "Digital Forensics": "digital-forensics",
  "Malware Analysis": "malware-analysis",
  "Threat Intelligence": "threat-intelligence",
  "Incident Response": "incident-response",
  "Cloud Security": "cloud-security",
  DevSecOps: "devsecops",
  "Container &amp; Kubernetes Security": "container-kubernetes-security",
  "Mobile Security": "mobile-security",
  "IoT &amp; Hardware Security": "iot-hardware-security",
  "OT / ICS Security": "ot-ics-security",
  "Database Security": "database-security",
  "AI Security": "ai-security",
  "Blockchain Security": "blockchain-security",
  "Governance, Risk &amp; Compliance": "grc",
  "Security Architecture": "security-architecture",
};

function addHeadingId(html, title, id) {
  const needle = `<h3>${title}</h3>`;
  const withId = `<h3 id="${id}">${title}</h3>`;
  if (html.includes(withId) || !html.includes(needle)) return html;
  return html.replace(needle, withId);
}

const files = fs.readdirSync(root).filter((name) => name.endsWith(".html"));
for (const name of files) {
  let html = fs.readFileSync(path.join(root, name), "utf8");
  html = stamp(html);
  if (name === "catalog.html") {
    for (const [title, id] of Object.entries(catalogIds)) html = addHeadingId(html, title, id);
  }
  if (name === "tools.html") {
    html = html.replace(/<article class="tool"([^>]*)>\s*<span class="tag">Proposed<\/span>\s*<h3>([^<]+)<\/h3>/g, (match, attrs, title) => {
      if (attrs.includes("id=")) return match;
      const id = title.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
      return `<article class="tool" id="${id}"${attrs}>\n            <span class="tag">Proposed</span>\n            <h3>${title}</h3>`;
    });
    html = html.replace(">Web</button>", ">Web &amp; API</button>");
    html = html.replace(">Offensive</button>", ">Red Team</button>");
    html = html.replace(">Defensive</button>", ">Blue Team</button>");
  }
  if (name === "range.html") {
    html = addHeadingId(html, "Virtual machines", "virtual-machines");
    html = addHeadingId(html, "CTF arena", "ctf");
    html = addHeadingId(html, "Red versus blue", "red-blue");
    if (!html.includes('id="soc"')) html = html.replace('<p class="kicker">SOC tracks</p>', '<p class="kicker" id="soc">SOC tracks</p>');
    if (!html.includes('id="forensics"')) html = html.replace('<p class="kicker">Evidence</p>', '<p class="kicker" id="forensics">Evidence</p>');
  }
  if (name === "pricing.html") {
    html = html.replace("These rates are a working proposal in US dollars.", "These rates are a working proposal in Indian rupees.");
    html = html.replace("$0", "₹0").replace("$199", "₹199").replace("$499", "₹499");
    html = html.replace('<article class="plan is-featured">', '<article class="plan is-featured" id="pro">');
    html = html.replace(/<article class="plan">(\s*<span class="tag">Proposed<\/span>\s*<h3>Free<\/h3>)/, '<article class="plan" id="free">$1');
    html = html.replace(/<article class="plan">(\s*<span class="tag">Proposed<\/span>\s*<h3>Elite<\/h3>)/, '<article class="plan" id="elite">$1');
  }
  fs.writeFileSync(path.join(root, name), html);
}

const pages = fs.readdirSync(root).filter((name) => name.endsWith(".html")).sort();
const urls = pages.map((name) => `  <url><loc>/${name === "index.html" ? "" : name}</loc></url>`).join("\n");
fs.writeFileSync(
  path.join(root, "sitemap.xml"),
  `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`
);
fs.writeFileSync(
  path.join(root, "robots.txt"),
  "User-agent: *\nAllow: /\n\nSitemap: /sitemap.xml\n"
);

console.log("Updated", pages.join(", "));
