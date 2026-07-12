import api from "./client";
import type { ApiResponse } from "@/types/api.types";
import type { CareerTrack, UserTrackEnrollment } from "@/types/track.types";

function unwrapApiData<T>(payload: ApiResponse<T> | T): T {
  if (payload && typeof payload === "object" && "data" in payload) {
    return (payload as ApiResponse<T>).data;
  }
  return payload as T;
}

export async function getTracks(category?: string): Promise<CareerTrack[]> {
  const params = category ? `?category=${category}` : "";
  const res = await api.get<ApiResponse<CareerTrack[]> | CareerTrack[]>(
    `/tracks/${params}`
  );
  return unwrapApiData<CareerTrack[]>(res.data);
}

export async function getTrack(slug: string): Promise<CareerTrack> {
  const res = await api.get<ApiResponse<CareerTrack> | CareerTrack>(
    `/tracks/${slug}/`
  );
  return unwrapApiData<CareerTrack>(res.data);
}

export async function enrollInTrack(slug: string): Promise<UserTrackEnrollment> {
  const res = await api.post<
    ApiResponse<UserTrackEnrollment> | UserTrackEnrollment
  >(`/tracks/${slug}/enroll/`);
  return unwrapApiData<UserTrackEnrollment>(res.data);
}

export async function getMyTracks(): Promise<UserTrackEnrollment[]> {
  const res = await api.get<
    ApiResponse<UserTrackEnrollment[]> | UserTrackEnrollment[]
  >("/tracks/mine/");
  return unwrapApiData<UserTrackEnrollment[]>(res.data);
}

export async function updateTrackProgress(slug: string): Promise<UserTrackEnrollment> {
  const res = await api.post<
    ApiResponse<UserTrackEnrollment> | UserTrackEnrollment
  >(`/tracks/${slug}/progress/`);
  return unwrapApiData<UserTrackEnrollment>(res.data);
}
