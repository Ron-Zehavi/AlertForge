import { useEffect, useState } from "react";

export default function App() {
  const [status, setStatus] = useState<string>("loading...");

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((d: { status: string }) => setStatus(d.status))
      .catch(() => setStatus("error"));
  }, []);

  return (
    <main style={{ fontFamily: "system-ui", padding: "2rem" }}>
      <h1>AlertForge</h1>
      <p>Outcome-aware follow-up prioritization for LSST alert streams</p>
      <p>
        API status: <strong>{status}</strong>
      </p>
    </main>
  );
}
