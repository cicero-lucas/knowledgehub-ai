import { api } from "./api";
import type { Document, PaginatedResponse } from "@/types";

export const documentsService = {
  async upload(file: File): Promise<Document> {
    const form = new FormData();
    form.append("file", file);
    const res = await api.post<Document>("/documents/", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  },

  async list(page = 1, pageSize = 20): Promise<PaginatedResponse<Document>> {
    const res = await api.get<PaginatedResponse<Document>>("/documents/", {
      params: { page, page_size: pageSize },
    });
    return res.data;
  },

  async get(id: string): Promise<Document> {
    const res = await api.get<Document>(`/documents/${id}`);
    return res.data;
  },

  async getStatus(id: string): Promise<Pick<Document, "id" | "status" | "error_message" | "page_count">> {
    const res = await api.get(`/documents/${id}/status`);
    return res.data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/documents/${id}`);
  },

  async reprocess(id: string): Promise<Document> {
    const res = await api.post<Document>(`/documents/${id}/reprocess`);
    return res.data;
  },
};
