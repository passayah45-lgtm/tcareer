import api from "./client";
import type { ApiResponse } from "@/types/api.types";
import type { CareerTrack, UserTrackEnrollment } from "@/types/track.types";

export async function getTracks(category?: string): Promise<CareerTrack[]> {
  const params = category ? `?category=${category}` : "";
  const res = await api.get<ApiResponse<CareerTrack[]>>(`/tracks/${params}`);
  return res.data.data as CareerTrack[];
}

export async function getTrack(slug: string): Promise<CareerTrack> {
  const res = await api.get<ApiResponse<CareerTrack>>(`/tracks/${slug}/`);
  return res.data.data;
}

export async function enrollInTrack(slug: string): Promise<UserTrackEnrollment> {
  const res = await api.post<ApiResponse<UserTrackEnrollment>>(
    `/tracks/${slug}/enroll/`
  );
  return res.data.data;
}

export async function getMyTracks(): Promise<UserTrackEnrollment[]> {
  const res = await api.get<ApiResponse<UserTrackEnrollment[]>>("/tracks/mine/");
  return res.data.data as UserTrackEnrollment[];
}

export async function updateTrackProgress(slug: string): Promise<UserTrackEnrollment> {
  const res = await api.post<ApiResponse<UserTrackEnrollment>>(
    `/tracks/${slug}/progress/`
  );
  return res.data.data;
}
