import { api } from "./api";
import type {
  Conversation,
  ConversationDetail,
  Message,
  PaginatedResponse,
} from "@/types";

export const conversationsService = {
  async create(data: {
    title?: string;
    document_ids?: string[];
  }): Promise<Conversation> {
    const res = await api.post<Conversation>("/conversations/", data);
    return res.data;
  },

  async list(page = 1, pageSize = 20): Promise<PaginatedResponse<Conversation>> {
    const res = await api.get<PaginatedResponse<Conversation>>("/conversations/", {
      params: { page, page_size: pageSize },
    });
    return res.data;
  },

  async get(id: string): Promise<ConversationDetail> {
    const res = await api.get<ConversationDetail>(`/conversations/${id}`);
    return res.data;
  },

  async ask(
    conversationId: string,
    question: string,
    documentIds?: string[]
  ): Promise<{ message: Message; sources: Message["sources"] }> {
    const res = await api.post(`/conversations/${conversationId}/messages`, {
      question,
      document_ids: documentIds,
    });
    return res.data;
  },

  async getMessages(conversationId: string): Promise<Message[]> {
    const res = await api.get<Message[]>(
      `/conversations/${conversationId}/messages`
    );
    return res.data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/conversations/${id}`);
  },
};
