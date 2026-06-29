import LegalLayout from "./LegalLayout";

export default function RefundPolicy() {
  return (
    <LegalLayout title="Refund Policy" lastUpdated="February 13, 2026">
      <p>
        We want you to be confident that MyCareerCopilot Pro is the right
        tool for your job search. This Refund Policy explains when and how
        refunds are issued.
      </p>

      <h2>1. Free Tier</h2>
      <p>
        The Free tier is offered at no charge. There is nothing to refund.
        You can use the Free tier indefinitely.
      </p>

      <h2>2. 7-Day Money-Back Guarantee</h2>
      <p>
        If you subscribe to MyCareerCopilot Pro and decide within{" "}
        <strong>7 days</strong> of your initial subscription charge that the
        Service is not right for you, email{" "}
        <a href="mailto:support@mycareercopilot.ca">support@mycareercopilot.ca</a>{" "}
        and we will issue a full refund of that initial charge.
      </p>
      <p>The 7-day guarantee:</p>
      <ul>
        <li>Applies only to the first month of a new Pro subscription</li>
        <li>Does not apply to renewals or to users who have previously subscribed and cancelled</li>
        <li>Cannot be combined with any promotional discount or free-trial extension already applied</li>
      </ul>

      <h2>3. Renewal Charges</h2>
      <p>
        Your Pro subscription renews automatically each month on the same
        calendar day. We send a renewal reminder before each charge. To
        avoid the next charge, cancel from the{" "}
        <a href="/billing">Billing</a> page (or by emailing us) <strong>before</strong> the renewal date. Renewal charges are{" "}
        <strong>non-refundable</strong> except in the cases described below.
      </p>

      <h2>4. Exceptions Where We Refund Renewals</h2>
      <p>
        We will refund a renewal charge in the following situations:
      </p>
      <ul>
        <li>
          <strong>Accidental renewal</strong> — you contact us within 72 hours
          of the renewal charge, you have not used any Pro feature during that
          billing period, and you have not been refunded under this exception
          previously.
        </li>
        <li>
          <strong>Service outage</strong> — the Service was materially
          unavailable for an extended period during the billing cycle (we may
          credit your account instead of refunding cash).
        </li>
        <li>
          <strong>Billing error</strong> — you were charged in error or charged
          more than the advertised price.
        </li>
        <li>
          <strong>Required by law</strong> — your local consumer protection
          laws require a refund.
        </li>
      </ul>

      <h2>5. How to Request a Refund</h2>
      <ol className="list-decimal pl-6 space-y-1 my-3 text-gray-700">
        <li>Email <a href="mailto:support@mycareercopilot.ca">support@mycareercopilot.ca</a> from the email address on your account.</li>
        <li>Include the date of the charge you want refunded and the reason for the request.</li>
        <li>We respond within 2 business days and process approved refunds within 5–10 business days.</li>
        <li>Refunds return to the original payment method (we cannot redirect them to a different card or account).</li>
      </ol>

      <h2>6. Cancellation vs. Refund</h2>
      <p>
        Cancelling your subscription stops future charges but does <strong>not</strong>{" "}
        refund past charges. If you want a refund of a past charge, request
        it explicitly under the rules above.
      </p>

      <h2>7. Chargebacks</h2>
      <p>
        If you have a billing concern, please contact us first — we will
        almost always resolve it directly and faster than a chargeback.
        Filing a chargeback without contacting us may result in your account
        being closed.
      </p>

      <h2>8. Contact</h2>
      <p>
        Email{" "}
        <a href="mailto:support@mycareercopilot.ca">support@mycareercopilot.ca</a>{" "}
        with any questions about this policy or a specific charge.
      </p>
    </LegalLayout>
  );
}
