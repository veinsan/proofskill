import type { ApiError } from "@/lib/api";
import { RingIcon } from "./icons";

/** A request problem in plain English with the API's code verbatim (no red: DESIGN.md Inputs / Error). */
export function Notice({ error, title }: { error: ApiError; title?: string }) {
  return (
    <div className="notice" role="alert">
      <RingIcon />
      <div>
        {title ? <strong>{title} </strong> : null}
        {error.message} <span className="mono">{error.code}</span>
      </div>
    </div>
  );
}

export function FieldError({ id, message, code }: { id: string; message: string; code?: string }) {
  return (
    <p className="field-error" id={id}>
      <RingIcon />
      <span>
        {message} {code ? <span className="mono">{code}</span> : null}
      </span>
    </p>
  );
}
