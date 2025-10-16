import { useEffect, useState } from "react";
import { verifyLicenseJWT, secondsLeft } from "../providers/LicenseProvider";

type Claims = {
  plan?: string;
  feat?: string[];   // features array from your JWT
  exp?: number;      // epoch seconds
  [k: string]: any;
};

export default function Chat() {
  const [status, setStatus] = useState<"loading" | "missing" | "invalid" | "valid">("loading");
  const [claims, setClaims] = useState<Claims | null>(null);

  useEffect(() => {
    const token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImxpY2Vuc2Utc2lnbmluZy1rZXkifQ.eyJpc3MiOiJodHRwczovL3NvZnRjaWFsLmNvbS8iLCJzdWIiOiIyOWZhYmJhOC05NmEyLTRhNWUtODY2My0wODg0MTY1NDllODQiLCJqdGkiOiJkNGU2NzU4MC1iYTBkLTQ1MWMtYTZhMy1hNGFiOWQxZDU4NGMiLCJpYXQiOjE3NjA1Mzc5NzksIm5iZiI6MTc2MDUzNzk3OSwiZXhwIjoxNzYwNTQxNTc5LCJwbGFuIjoicHJvIiwic2VhdHMiOjEsImZlYXQiOiJbXCJ0ZXN0XCIsIFwiZm9vXCJdIiwiYWN0IjoiMzQ4MWZiOTctZTAzNS00OWFiLWFhYzMtNTJjODhmNTQ1NjQxIn0.vaK7SuInibdpjxZGYI9XuwH_AOCXk19lVGc2jwaw7sQjmVtIWEk2ZP623JmADbCsd2kk3SgI0hEQa3AyZJUfeU8GwcBh1eWVCHSDGpNW2WiqqLHsYlZA_v1AFtK2OGVsGo3HcCTJGBaFobQtKDzxgvzi6ANSGwhrOwY8v_Cj9zSweGAGUIsPPW-UzTL598haWjDJ0NiqBjOrcRG05C9r7ylwoYN2RW-DA_JghWTvXRT9bhhvLn8vvXMhvWUDKMCFgF3HKe_dKPMKKmiVaoMF4xiYpavCuMQIjZIwW5mA-hMNAcci50sO9BOIpsqZIQafhgDFPXuG47T-_23a0FaCXA"; // <-- adjust later
    if (!token) {
      setStatus("missing");
      return;
    }

    (async () => {
      try {
        const payload = await verifyLicenseJWT(token); // throws if invalid/expired
        setClaims(payload as Claims);
        setStatus("valid");
      } catch {
        setStatus("invalid");
      }
    })();
  }, []);

  // UI helpers
  const Banner = ({ text }: { text: string }) => (
    <div className="w-full rounded-xl border border-red-300 bg-red-50 text-red-700 px-4 py-3 mb-4">
      <strong className="font-semibold">License issue: </strong>
      <span>{text}</span>
    </div>
  );

  if (status === "loading") {
    return <div className="text-sm text-gray-500">Checking license…</div>;
  }

  if (status === "missing") {
    return <Banner text="No license token found. Please activate to unlock features." />;
  }

  if (status === "invalid") {
    return <Banner text="Your license token is invalid or expired. Please re-activate." />;
  }

  // status === "valid"
  const plan = claims?.plan ?? "unknown";
  const raw = claims?.feat as unknown;
  const features: string[] =
    Array.isArray(raw)
      ? raw
      : (typeof raw === "string"
          ? (() => { try { return JSON.parse(raw); } catch { return []; } })()
          : []);
  const secs = (() => {
    const t = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImxpY2Vuc2Utc2lnbmluZy1rZXkifQ.eyJpc3MiOiJodHRwczovL3NvZnRjaWFsLmNvbS8iLCJzdWIiOiIyOWZhYmJhOC05NmEyLTRhNWUtODY2My0wODg0MTY1NDllODQiLCJqdGkiOiJkNGU2NzU4MC1iYTBkLTQ1MWMtYTZhMy1hNGFiOWQxZDU4NGMiLCJpYXQiOjE3NjA1Mzc5NzksIm5iZiI6MTc2MDUzNzk3OSwiZXhwIjoxNzYwNTQxNTc5LCJwbGFuIjoicHJvIiwic2VhdHMiOjEsImZlYXQiOiJbXCJ0ZXN0XCIsIFwiZm9vXCJdIiwiYWN0IjoiMzQ4MWZiOTctZTAzNS00OWFiLWFhYzMtNTJjODhmNTQ1NjQxIn0.vaK7SuInibdpjxZGYI9XuwH_AOCXk19lVGc2jwaw7sQjmVtIWEk2ZP623JmADbCsd2kk3SgI0hEQa3AyZJUfeU8GwcBh1eWVCHSDGpNW2WiqqLHsYlZA_v1AFtK2OGVsGo3HcCTJGBaFobQtKDzxgvzi6ANSGwhrOwY8v_Cj9zSweGAGUIsPPW-UzTL598haWjDJ0NiqBjOrcRG05C9r7ylwoYN2RW-DA_JghWTvXRT9bhhvLn8vvXMhvWUDKMCFgF3HKe_dKPMKKmiVaoMF4xiYpavCuMQIjZIwW5mA-hMNAcci50sO9BOIpsqZIQafhgDFPXuG47T-_23a0FaCXA";
    return t ? Math.max(0, secondsLeft(t)) : 0;
  })();

  return (
    <div className="space-y-3">
      <div className="inline-flex items-center gap-2 rounded-2xl border px-3 py-1 shadow-sm">
        <span className="text-xs uppercase tracking-wide text-white">Plan</span>
        <span className="text-sm font-medium text-white">{plan}</span>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs uppercase tracking-wide text-white">Features</span>
        {features.length > 0 ? (
          features.map((f) => (
            <span key={f} className="rounded-full border px-2 py-0.5 text-sm text-white">
              {f}
            </span>
          ))
        ) : (
          <span className="text-sm text-white">none</span>
        )}
      </div>

      <div className="text-xs text-white">
        Token valid for ~{Math.ceil(secs / 60)} min
      </div>
    </div>
  );
}
