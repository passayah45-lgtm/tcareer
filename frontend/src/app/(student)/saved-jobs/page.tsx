"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import { createSavedJobCollection, getSavedJobCollections, getSavedJobs, removeSavedJob } from "@/lib/api/student-career.api";
import type { SavedJob, SavedJobCollection } from "@/types/student-career.types";

export default function SavedJobsPage() {
  const [saved, setSaved] = useState<SavedJob[]>([]);
  const [collections, setCollections] = useState<SavedJobCollection[]>([]);
  const [collectionName, setCollectionName] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [savedData, collectionData] = await Promise.all([getSavedJobs(), getSavedJobCollections()]);
      setSaved(savedData);
      setCollections(collectionData);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function addCollection(event: FormEvent) {
    event.preventDefault();
    if (!collectionName.trim()) return;
    await createSavedJobCollection({ name: collectionName.trim() });
    setCollectionName("");
    await load();
  }

  async function remove(jobId: string) {
    await removeSavedJob(jobId);
    await load();
  }

  return (
    <>
      <Navbar />
      <main className="max-w-6xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="lg:col-span-2 space-y-4">
          <div>
            <h1 className="text-2xl font-bold">Saved jobs</h1>
            <p className="text-sm text-muted-foreground mt-1">Compare jobs, favorite companies, and prepare future alerts.</p>
          </div>
          {loading && <div className="h-52 bg-muted rounded-xl animate-pulse" />}
          {!loading && saved.length === 0 && <div className="border border-border rounded-xl bg-card p-10 text-center">No saved jobs yet.</div>}
          {saved.map((item) => (
            <article key={item.id} className="border border-border rounded-xl bg-card p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="font-semibold">{item.job.title}</h2>
                  <p className="text-sm text-muted-foreground">{item.job.company_name} - {item.job.location}</p>
                  <p className="text-sm text-primary mt-1">{item.job.salary_display}</p>
                  {item.collection_name && <span className="tag mt-3">{item.collection_name}</span>}
                </div>
                <div className="flex gap-2">
                  <Link href={`/jobs/${item.job.id}`} className="btn-sm btn-primary">Open</Link>
                  <button onClick={() => remove(item.job.id)} className="btn-sm btn-secondary">Remove</button>
                </div>
              </div>
            </article>
          ))}
        </section>
        <aside className="border border-border rounded-xl bg-card p-5 h-fit">
          <h2 className="font-semibold mb-4">Collections and alerts</h2>
          <form onSubmit={addCollection} className="flex gap-2 mb-4">
            <input className="input" value={collectionName} onChange={(e) => setCollectionName(e.target.value)} placeholder="Collection name" />
            <button className="btn-base btn-primary">Add</button>
          </form>
          <div className="space-y-2">
            {collections.map((collection) => (
              <div key={collection.id} className="border border-border rounded-lg p-3">
                <p className="text-sm font-medium">{collection.name}</p>
                <p className="text-xs text-muted-foreground">{collection.saved_count} saved jobs</p>
              </div>
            ))}
          </div>
          <div className="mt-5 border-t border-border pt-4">
            <p className="text-sm font-medium">Job alerts foundation</p>
            <p className="text-xs text-muted-foreground mt-1">Alerts are ready in the API and can be connected to email or push delivery in a later pass.</p>
          </div>
        </aside>
      </main>
    </>
  );
}
