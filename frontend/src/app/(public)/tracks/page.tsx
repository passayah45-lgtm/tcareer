import { Navbar } from "@/components/layout/Navbar";
import { TrackCard } from "@/components/tracks/TrackCard";
import type { CareerTrack } from "@/types/track.types";

export const dynamic = "force-dynamic";

async function fetchTracks(): Promise<CareerTrack[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) return [];
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  try {
    const res = await fetch(
      `${apiUrl}/tracks/`,
      { next: { revalidate: 300 }, signal: controller.signal }
    );
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : (data.data as CareerTrack[]) || [];
  } catch {
    return [];
  } finally {
    clearTimeout(timeout);
  }
}

const categoryGroups: Record<string, string> = {
  tech: "Tech and Engineering",
  data_ai: "Data and AI",
  design: "Design and Product",
  business: "Business and Marketing",
};

export default async function TracksPage() {
  const tracks = await fetchTracks();

  const grouped = Object.entries(categoryGroups).map(([key, label]) => ({
    key,
    label,
    tracks: tracks.filter((t) => t.category === key),
  })).filter((g) => g.tracks.length > 0);

  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Career Tracks</h1>
          <p className="text-muted-foreground">
            Structured learning paths from beginner to job-ready. Each track
            combines the right courses in the right order.
          </p>
        </div>

        <div className="space-y-10">
          {grouped.map(({ key, label, tracks: groupTracks }) => (
            <section key={key}>
              <h2 className="text-lg font-semibold mb-4">{label}</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {groupTracks.map((track) => (
                  <TrackCard key={track.id} track={track} />
                ))}
              </div>
            </section>
          ))}
        </div>

        {tracks.length === 0 && (
          <div className="text-center py-16 text-muted-foreground">
            <p>Career tracks are being set up. Check back soon.</p>
          </div>
        )}
      </main>
    </>
  );
}
