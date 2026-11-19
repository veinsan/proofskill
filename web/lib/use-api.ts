"use client";

import { useEffect, useRef, useState } from "react";
import type { ApiError, ApiResult } from "./api";

export type Load<T> = { state: "loading" } | { state: "ok"; data: T } | { state: "error"; error: ApiError };

/** Runs `load` on mount and whenever `key` changes; `reload` runs it again. */
export function useApi<T>(load: () => Promise<ApiResult<T>>, key: string): { result: Load<T>; reload: () => void } {
  const [result, setResult] = useState<Load<T>>({ state: "loading" });
  const [tick, setTick] = useState(0);
  const latest = useRef(load);

  useEffect(() => {
    latest.current = load;
  });

  useEffect(() => {
    let live = true;
    latest.current().then((response) => {
      if (live) setResult(response.ok ? { state: "ok", data: response.data } : { state: "error", error: response.error });
    });
    return () => {
      live = false;
    };
  }, [key, tick]);

  return { result, reload: () => setTick((n) => n + 1) };
}
