// Operation ids come from the API, so new modes need no client edit.
export type OperationId = string;

export type JobStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface User {
  id: string;
  email: string;
  name: string | null;
  isGuest: boolean;
  createdAt: number | null;
}

export interface LogoutResponse {
  logoutUrl: string | null;
}

export interface Operation {
  id: OperationId;
  label: string;
  description: string;
  group: string;
  inputExtensions: string[];
  outputExtension: string;
  outputSuffix: string;
}

export interface Conversion {
  id: string;
  operation: OperationId;
  operationLabel: string;
  originalFilename: string;
  status: JobStatus;
  errorMessage: string | null;
  fileSize: number;
  outputSize: number | null;
  outputFilename: string | null;
  uploadCompleted: boolean;
  downloadAvailable: boolean;
  downloadRequiresAccount: boolean;
  attempts: number;
  createdAt: number | null;
  startedAt: number | null;
  completedAt: number | null;
  expiresAt: number | null;
}

export interface UploadTicket {
  url: string;
  method: "PUT";
  headers: Record<string, string>;
  expiresAt: number;
}

export interface CreateConversionResponse {
  job: Conversion;
  upload: UploadTicket;
}

export interface DownloadTicket {
  url: string;
  expiresAt: number;
}

export interface ApiErrorBody {
  error?: string;
  details?: unknown;
}
