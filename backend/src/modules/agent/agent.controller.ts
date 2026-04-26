import { Controller, Get, Req, Post, Body, Param, Res } from '@nestjs/common';
import { Response, Request } from 'express';
import { AgentService } from './agent.service';
import { ApiTags } from '@nestjs/swagger';
import { GetUser } from '../auth/decorator/get-user.decorator';
import { ChatDto } from './dto/chat.dto';
import axios from 'axios';
import { Readable } from 'stream';

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
      const userId = `caa8293b-8d8f-48ea-ab5f-a1d354a88077`;
      const cleanPayload: ChatDto = {
        message: body.message,
        ...(body.thread_id?.trim() ? { thread_id: body.thread_id.trim() } : {}),
      };

      res.setHeader('Content-Type', 'text/event-stream');
      res.setHeader('Cache-Control', 'no-cache');
      res.setHeader('Connection', 'keep-alive');

      res.flushHeaders();
      console.log(cleanPayload);

      const fastApiResponse = await axios<Readable>({
        method: 'POST',
        url: 'http://localhost:8000/chat/stream',
        data: {
          user_id: userId,
          ...cleanPayload,
        },
        responseType: 'stream',
      });
      console.log(fastApiResponse.data);
      let threadId: string;
      fastApiResponse.data.on('data', (chunk: Buffer) => {
        const line = chunk.toString();

        // SSE format itu "data: {...}\n\n"
        if (line.includes('data:')) {
          try {
            // Ambil bagian JSON-nya saja
            const jsonStr = line.split('data: ')[1]?.split('\n')[0];
            if (jsonStr) {
              // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
              const data = JSON.parse(jsonStr);
              // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
              threadId = data?.thread_id;
              if (threadId) {
                console.log('DAPET THREAD ID-NYA:', threadId);
                // Kamu bisa simpan ke DB Session di sini secara async
              }
            }
          } catch (e) {
            // Abaikan kalau chunk-nya parsial/potongan
          }
        }
      });
      fastApiResponse.data.on('end', () => {
        // Disini kamu bisa update status Session di Prisma jadi "waiting_hitl" atau "done"
        const newPayload = {
          ...cleanPayload,
          thread_id: threadId,
        };
        void this.agentService.createSession(newPayload, userId);
      });

      req.on('close', () => {
        // Kalau user tutup browser di tengah jalan, matikan stream dari FastAPI
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
