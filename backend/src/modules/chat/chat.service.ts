import { Injectable } from '@nestjs/common';

@Injectable()
export class ChatService {
  async sendMessage(payload: any) {
    // TODO: Forward to Python Agent Orchestrator
    // For now, return mock response to satisfy frontend
    return {
      role: 'ai',
      content: 'Hello! I am the mock backend AI. The Python service is not yet connected.',
    };
  }
}
