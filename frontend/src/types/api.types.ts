export interface ApiResponse<T> {
  success: boolean;
  data: T;
  errors: Record<string, string | string[]>;
  meta: {
    count?: number;
    next?: string | null;
    previous?: string | null;
    page?: number;
    page_size?: number;
    pipeline_statistics?: Record<string, number>;
  };
}

export interface PaginatedData<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  detail?: string;
  code?: string;
  [key: string]: string | string[] | undefined;
}
