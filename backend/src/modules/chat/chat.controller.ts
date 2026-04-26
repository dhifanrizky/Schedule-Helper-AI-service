import { Controller, Post, Body, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth, ApiResponse } from '@nestjs/swagger';
import { ChatService } from './chat.service.js';
import { JwtGuard } from '../auth/guard/jwt.guard.js';

@ApiTags('chat')
@ApiBearerAuth()
@UseGuards(JwtGuard)
@Controller('chat')
export class ChatController {
  constructor(private readonly chatService: ChatService) {}

  @Post('send')
  @ApiOperation({ summary: 'Send message to AI Orchestrator' })
  @ApiResponse({ status: 200, description: 'Message processed' })
  sendMessage(@Body() payload: any) {
    return this.chatService.sendMessage(payload);
  }
}
