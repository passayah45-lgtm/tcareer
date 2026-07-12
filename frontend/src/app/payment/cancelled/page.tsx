import Link from "next/link";
export default function PaymentCancelledPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-sm text-center">
        <div className="text-6xl mb-4">↩</div>
        <h1 className="text-2xl font-bold mb-2">Payment cancelled</h1>
        <p className="text-muted-foreground text-sm mb-6">No charge was made. You can subscribe anytime.</p>
        <Link href="/subscribe" className="bg-primary text-primary-foreground px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors">Try again</Link>
      </div>
    </div>
  );
}
