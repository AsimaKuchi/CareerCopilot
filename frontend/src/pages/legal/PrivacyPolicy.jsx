import LegalLayout from "./LegalLayout";

export default function PrivacyPolicy() {
  return (
    <LegalLayout title="Privacy Policy" lastUpdated="February 13, 2026">
      <p>
        MyCareerCopilot (&quot;we&quot;, &quot;us&quot;, &quot;our&quot;) operates the website at{" "}
        <a href="https://mycareercopilot.ca">mycareercopilot.ca</a> and the
        MyCareerCopilot Chrome browser extension (collectively, the
        &quot;Service&quot;). This Privacy Policy explains what information we collect,
        how we use it, who we share it with, and the rights you have.
      </p>

      <h2>1. Single Purpose &amp; What the Service Does</h2>
      <p>
        MyCareerCopilot is an AI-assisted career management platform. The
        Service helps you discover job opportunities that match your skills,
        tailor application materials (resumes and cover letters) to specific
        roles, prepare for interviews, and explore career paths. The
        accompanying Chrome extension helps you autofill repetitive job
        application forms on supported job boards. We do not perform actions on
        your behalf without your explicit click-through approval.
      </p>

      <h2>2. Information We Collect</h2>

      <h3>2.1 Account information you provide</h3>
      <ul>
        <li>Name, email address, and password (encrypted at rest)</li>
        <li>Authentication identifier from Google when you sign in with Google</li>
        <li>Optional profile information: phone, address, work authorization status, links to LinkedIn/portfolio</li>
        <li>Resume file uploads (PDF / DOCX) and the parsed text extracted from them</li>
        <li>Job application history and notes you create</li>
        <li>Saved job listings and career path selections</li>
      </ul>

      <h3>2.2 Information collected automatically</h3>
      <ul>
        <li>Session cookies needed to keep you signed in (HttpOnly, Secure, SameSite)</li>
        <li>CSRF security tokens</li>
        <li>IP address and basic browser metadata, used only for security (rate limiting, brute-force detection)</li>
        <li>Audit logs of significant account activity (logins, failed login attempts, admin actions)</li>
        <li>Per-feature monthly usage counters to enforce free-tier limits</li>
      </ul>

      <h3>2.3 Information collected by the Chrome extension</h3>
      <ul>
        <li>The URL of the job posting you are viewing at the moment you click the extension icon</li>
        <li>The structure of the application form being filled (field labels, not other users&apos; data)</li>
        <li>The values pulled from your account profile that are written into the form on your click</li>
      </ul>
      <p>
        The extension <strong>does not</strong> read or transmit pages you visit
        when the extension is idle. It only activates when you click the
        extension icon on a recognized job application page.
      </p>
      <h3>2.3.1 Chrome extension permissions explained</h3>
      <ul>
        <li><strong>activeTab / scripting</strong> — used only to read the form fields on the job application page you are viewing and fill them with your profile data when you click &quot;Autofill&quot;.</li>
        <li><strong>storage</strong> — stores your extension preferences locally in your browser.</li>
        <li><strong>cookies</strong> — used solely to read your MyCareerCopilot session cookie so the extension can securely fetch your own profile. No other sites&apos; cookies are accessed.</li>
        <li><strong>Host permissions (all sites)</strong> — job applications live on thousands of different career sites and ATS platforms (Workday, Greenhouse, Lever, etc.), so the extension must be able to run on the page you invoke it on. It never runs automatically in the background.</li>
      </ul>
      <p>
        Use of information received from the extension adheres to the Chrome
        Web Store User Data Policy, including the Limited Use requirements.
      </p>

      <h3>2.4 Payment information</h3>
      <p>
        Payments are processed by <strong>Stripe</strong>. We never see or
        store your full credit card number, CVV, or bank account number. Stripe
        provides us only a customer ID, your subscription status, and the last
        four digits of the card for receipt purposes.
      </p>

      <h2>3. How We Use Your Information</h2>
      <ul>
        <li>To create and maintain your account</li>
        <li>To autofill job applications on your explicit request</li>
        <li>To generate AI-tailored resumes, cover letters, interview prep, and career path recommendations</li>
        <li>To process subscription payments and send billing receipts</li>
        <li>To send transactional emails (welcome, password reset, email verification, subscription notices)</li>
        <li>To protect the Service against abuse, fraud, and brute-force attacks</li>
        <li>To comply with legal obligations</li>
      </ul>
      <p>
        We do <strong>not</strong> use your data for marketing to third parties.
        We do <strong>not</strong> sell your data. We do <strong>not</strong>{" "}
        train AI models on your resume content or application history.
      </p>

      <h2>4. Service Providers We Share Data With</h2>
      <p>
        We use a small number of trusted third-party processors to operate the
        Service. Each receives only the data needed for its specific function:
      </p>
      <ul>
        <li>
          <strong>Stripe</strong> — payment processing. Sees your billing info
          and email. Their privacy policy is at{" "}
          <a href="https://stripe.com/privacy" target="_blank" rel="noopener noreferrer">stripe.com/privacy</a>.
        </li>
        <li>
          <strong>Resend</strong> — transactional email delivery. Sees your
          email address and the content of the emails we send you (welcome,
          password reset, etc.).
        </li>
        <li>
          <strong>OpenAI</strong> and <strong>Anthropic</strong> — power our AI
          features (resume tailoring, interview prep, career coach). Snippets of
          your profile and the specific prompt for each request are sent.
          OpenAI / Anthropic state in their API terms that they do not train
          their models on API-submitted data.
        </li>
        <li>
          <strong>Google OAuth</strong> — only if you choose to sign in with
          Google. Google sees only that you used your Google account to log in.
          We receive your name, email, and Google account ID.
        </li>
        <li>
          <strong>JSearch (RapidAPI)</strong> — used to discover job listings
          across multiple job boards. We send only the search query you enter.
        </li>
        <li>
          <strong>MongoDB Atlas</strong> — encrypted database hosting for your
          account and content. Hosted in North America.
        </li>
      </ul>
      <p>
        We do not share your data with advertisers, data brokers, or
        marketing networks.
      </p>

      <h2>5. Data Security</h2>
      <ul>
        <li>All connections to and from the Service use HTTPS (TLS 1.2+).</li>
        <li>Passwords are hashed with bcrypt (industry standard).</li>
        <li>Sensitive profile fields (e.g., resume text, phone, address) are encrypted at rest in our database.</li>
        <li>Session cookies are HttpOnly, Secure, and SameSite to mitigate XSS and CSRF.</li>
        <li>The application has a CSRF middleware that rejects state-changing requests without a matching CSRF token.</li>
        <li>Rate limiting and account lockout protect against brute-force attacks.</li>
        <li>Admin actions are recorded in audit logs.</li>
      </ul>
      <p>
        No system is perfectly secure. If we ever discover a breach involving
        your personal information, we will notify you by email within 72 hours
        of confirming it.
      </p>

      <h2>6. Data Retention</h2>
      <ul>
        <li>While your account is active, we retain your data so the Service can function.</li>
        <li>You can request deletion of your account and all associated data at any time by emailing <a href="mailto:support@mycareercopilot.ca">support@mycareercopilot.ca</a>. Deletion is completed within 30 days.</li>
        <li>Some records (audit logs, payment receipts) may be retained for up to 7 years to comply with tax and accounting laws.</li>
        <li>Backup snapshots are retained for up to 30 days after deletion before being purged.</li>
      </ul>

      <h2>7. Your Rights</h2>
      <p>
        Depending on where you live, you may have the following rights under
        laws such as GDPR (EU/UK), PIPEDA (Canada), and CCPA/CPRA (California):
      </p>
      <ul>
        <li>Right to <strong>access</strong> a copy of your data</li>
        <li>Right to <strong>correct</strong> inaccurate data</li>
        <li>Right to <strong>delete</strong> your account and data</li>
        <li>Right to <strong>port</strong> your data to another service in a machine-readable format</li>
        <li>Right to <strong>object</strong> to certain processing</li>
        <li>Right to <strong>withdraw consent</strong> at any time (where processing is based on consent)</li>
      </ul>
      <p>
        To exercise any of these rights, email{" "}
        <a href="mailto:support@mycareercopilot.ca">support@mycareercopilot.ca</a>.
        We respond within 30 days.
      </p>

      <h2>8. Children&apos;s Privacy</h2>
      <p>
        MyCareerCopilot is not directed at children under 16. We do not
        knowingly collect personal information from children under 16. If you
        believe a child has provided us information, contact us and we will
        delete it.
      </p>

      <h2>9. Cookies &amp; Tracking</h2>
      <p>
        We use only the cookies strictly necessary to operate the Service:
        the session cookie that keeps you signed in, and the CSRF cookie that
        protects against cross-site request forgery. We do not use
        third-party advertising or tracking cookies, and we do not employ
        analytics scripts that fingerprint your device.
      </p>

      <h2>10. International Data Transfers</h2>
      <p>
        MyCareerCopilot is operated from Canada. Some of our service providers
        (Stripe, OpenAI, Anthropic, Resend) operate primarily in the United
        States. When your information is transferred internationally, we rely
        on appropriate safeguards including standard contractual clauses where
        required by law.
      </p>

      <h2>11. Changes to This Policy</h2>
      <p>
        We may update this Privacy Policy from time to time. When we make a
        material change, we will notify you by email (using the address
        associated with your account) and update the &quot;Last updated&quot; date at
        the top of this page at least 14 days before the change takes effect.
      </p>

      <h2>12. Contact Us</h2>
      <p>
        If you have any questions about this Privacy Policy or our data
        practices, contact us at{" "}
        <a href="mailto:support@mycareercopilot.ca">support@mycareercopilot.ca</a>.
      </p>
      <p>
        <strong>Data Controller:</strong> MyCareerCopilot, Canada
      </p>
    </LegalLayout>
  );
}
