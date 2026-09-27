/**
 * Shown with every generated/saved plan: the project's non-negotiable
 * educational-only framing.
 */
export default function DisclaimerBanner({ compact = false }) {
  return (
    <div className={compact ? "disclaimer disclaimer-compact" : "disclaimer"}>
      ⚠️ Educational/general wellness example generated from demo data —{" "}
      <strong>not medical or clinical nutrition advice.</strong> Consult a
      qualified professional for personal guidance.
    </div>
  );
}
