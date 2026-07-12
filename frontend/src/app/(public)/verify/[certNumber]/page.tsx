interface CertVerification {
  valid: boolean;
  reason: string;
  certificate: {
    cert_number: string;
    student_name: string;
    course_title: string;
    issued_at: string;
    pdf_url: string;
  } | null;
}

async function verifyCert(certNumber: string): Promise<CertVerification> {
  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/certificates/verify/${certNumber}/`,
      { cache: "no-store" }
    );
    const json = await res.json();
    // Handle wrapped response {success, data} and flat response
    const data = json.data || json;
    return {
      valid: data.valid ?? false,
      reason: data.reason ?? "",
      certificate: data.certificate ?? null,
    };
  } catch {
    return {
      valid: false,
      reason: "Verification service unavailable.",
      certificate: null,
    };
  }
}

export default async function VerifyPage({
  params,
}: {
  params: { certNumber: string };
}) {
  const result = await verifyCert(params.certNumber);

  return (
    <div className="min-h-screen bg-muted/30 flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full">
        <div className="text-center mb-6">
          <h1 className="text-xl font-semibold">T-Career Certificate Verification</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Official verification from the T-Career platform
          </p>
        </div>

        <div className="bg-background border rounded-xl overflow-hidden">
          {result.valid && result.certificate ? (
            <>
              <div className="bg-green-500 px-6 py-4 flex items-center gap-3">
                <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center text-green-500 font-bold">
                  ✓
                </div>
                <div>
                  <p className="text-white font-semibold">Certificate Valid</p>
                  <p className="text-green-100 text-sm">This certificate is authentic</p>
                </div>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                    Awarded to
                  </p>
                  <p className="text-lg font-semibold">{result.certificate.student_name}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                    Course completed
                  </p>
                  <p className="font-medium">{result.certificate.course_title}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                    Issue date
                  </p>
                  <p className="text-sm">
                    {new Date(result.certificate.issued_at).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                    Certificate ID
                  </p>
                  <p className="text-sm font-mono">{result.certificate.cert_number}</p>
                </div>
                {result.certificate.pdf_url && (
                  
                   <a href={result.certificate.pdf_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full text-center border rounded-lg py-2 text-sm hover:bg-muted transition-colors mt-2"
                  >
                    Download PDF certificate
                  </a>
                )}
              </div>
            </>
          ) : (
            <>
              <div className="bg-red-500 px-6 py-4 flex items-center gap-3">
                <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center text-red-500 font-bold">
                  ✗
                </div>
                <div>
                  <p className="text-white font-semibold">Certificate Invalid</p>
                  <p className="text-red-100 text-sm">This certificate could not be verified</p>
                </div>
              </div>
              <div className="p-6">
                <p className="text-sm text-muted-foreground">
                  {result.reason || "No certificate found with this ID."}
                </p>
                <p className="text-sm text-muted-foreground mt-3">
                  Certificate ID checked:{" "}
                  <span className="font-mono">{params.certNumber}</span>
                </p>
              </div>
            </>
          )}
        </div>

        <p className="text-center text-xs text-muted-foreground mt-4">
          Verified by T-Career platform
        </p>
      </div>
    </div>
  );
}