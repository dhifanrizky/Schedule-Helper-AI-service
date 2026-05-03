/* eslint-disable 
  @typescript-eslint/no-unsafe-assignment,
  @typescript-eslint/no-unsafe-member-access
*/

import { Controller, Get, Req, Post, Body, Param, Res } from '@nestjs/common';
import { Response, Request } from 'express';
import { AgentService } from './agent.service';
import { ApiTags } from '@nestjs/swagger';
import { ChatDto } from './dto/chat.dto';
import axios from 'axios';
import { Readable } from 'stream';
import { RouterType } from './types/agent-output.type';

@ApiTags('agent')
// @ApiBearerAuth()
// @UseGuards(JwtGuard)
@Controller('agent')
export class AgentController {
  constructor(private readonly agentService: AgentService) {}

  @Post('stream')
  async stream(
    @Body() body: ChatDto,
    @Res() res: Response,
    @Req() req: Request,
  ) {
    try {
      const userId = 'caa8293b-8d8f-48ea-ab5f-a1d354a88077';

      const cleanPayload: ChatDto = {
        message: body.message,
        ...(body.thread_id?.trim() ? { thread_id: body.thread_id.trim() } : {}),
      };
      console.log(cleanPayload, body.approved_data);
      res.setHeader('Content-Type', 'text/event-stream');
      res.setHeader('Cache-Control', 'no-cache');
      res.setHeader('Connection', 'keep-alive');

      res.flushHeaders();

      const isResume = !!cleanPayload.thread_id;

      const fastApiResponse = await axios<Readable>({
        method: 'POST',
        url: isResume
          ? `${process.env.AI_API ?? 'http://localhost:8000'}/resume/${cleanPayload.thread_id}/stream`
          : `${process.env.AI_API ?? 'http://localhost:8000'}/chat/stream`,
        data: isResume
          ? {
              user_id: userId,
              approved_data: body.approved_data,
            }
          : {
              user_id: userId,
              thread_id: cleanPayload.thread_id,
              message: cleanPayload.message,
            },
        responseType: 'stream',
      });

      let sessionThreadId = cleanPayload.thread_id;
      let status: string | undefined;
      let routerData: RouterType | undefined;
      let aiMessage: string | undefined;
      let buffer = '';

      fastApiResponse.data.on('data', (chunk: Buffer) => {
        buffer += chunk.toString();

        const events = buffer.split('\n\n');

        buffer = events.pop() ?? '';

        for (const eventBlock of events) {
          try {
            const lines = eventBlock.split('\n');

            let eventType = '';
            let jsonStr = '';

            for (const line of lines) {
              if (line.startsWith('event:')) {
                eventType = line.replace('event:', '').trim();
              }

              if (line.startsWith('data:')) {
                jsonStr += line.replace('data:', '').trim();
              }
            }

            if (!jsonStr) continue;

            const data = JSON.parse(jsonStr);

            if (data?.thread_id) {
              sessionThreadId = data.thread_id;
            }

            if (eventType === 'agent_step' && data?.update?.node === 'router') {
              routerData = data.update.update;
            }

            if (eventType === 'execution_complete') {
              status = data.status;
              aiMessage = data?.hitl_payload?.draft;
            }
          } catch (error) {
            console.error('SSE parse error:', error);
          }
        }
      });

      fastApiResponse.data.on('end', () => {
        if (!sessionThreadId) return;

        const payload: ChatDto = {
          ...cleanPayload,
          thread_id: sessionThreadId,
        };

        void this.agentService.upsertSession(
          payload,
          userId,
          status,
          routerData?.current_intent,
          aiMessage,
        );

        if (routerData?.raw_tasks?.length) {
          void this.agentService.upsertRawTask(userId, routerData.raw_tasks);
        }
      });

      req.on('close', () => {
        fastApiResponse.data.destroy();
      });

      fastApiResponse.data.pipe(res);

      return res;
    } catch (error) {
      if (!res.headersSent) {
        res.status(500).json({
          message: `Error connecting to AI server ${String(error)}`,
        });
      }
    }
  }

  @Get()
  findAll() {
    return this.agentService.findAll();
  }

  @Get(':id')
  findOne(@Param('id') id: string) {
    return this.agentService.findOne(+id);
  }
}
