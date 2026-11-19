import type { CredentialView } from "@/lib/api";
import { formatDate, formatDateTime } from "@/lib/format";
import { Pass, RegistryStub, SkillChips } from "./pass";

/** The issuer's and holder's view of a credential: every field, with the registry status stub. */
export function CredentialPass({ view }: { view: CredentialView }) {
  return (
    <Pass
      issuerId={view.issuer.issuerId}
      issuerName={view.issuer.name}
      credentialId={view.credentialId}
      credentialSub={`Issued ${formatDateTime(view.issuedAt)}`}
      cleared={view.status === "active"}
      cells={[
        { label: "Program", value: view.program.title, full: true },
        { label: "Completed", value: formatDate(view.program.completedAt) },
        {
          label: "Holder",
          value: (
            <>
              {view.holderDisplayName} <span className="mono muted">{view.holderRef}</span>
            </>
          ),
        },
        { label: "Pass criteria", value: view.program.criteria, full: true },
        { label: "Skills, from the issuer's catalog", value: <SkillChips skills={view.skills} />, full: true },
      ]}
      stub={
        <RegistryStub
          status={view.status}
          issuerId={view.issuer.issuerId}
          revokedAt={view.revokedAt}
          reason={view.revocationReason}
          txHash={view.txHash}
          commitment={view.commitment}
        />
      }
    />
  );
}
