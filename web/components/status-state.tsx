import type { CredentialStatus } from "@/lib/api";
import { DotIcon, RingIcon } from "./icons";

/** Credential status as a word and a fill (dot or ring), never a hue (Two-Ink State Rule). */
export function StatusState({ status }: { status: CredentialStatus }) {
  return (
    <span className={status === "active" ? "state state--active" : "state"}>
      {status === "active" ? <DotIcon size={10} /> : <RingIcon size={10} />}
      {status}
    </span>
  );
}
