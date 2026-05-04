import {
  ConflictException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { ChatDto } from './dto/chat.dto';
import { PrismaService } from '../prisma/prisma.service';
import {
  BadRequestException,
  InternalServerErrorException,
} from '@nestjs/common';
import { Prisma } from '@prisma/client';
import { RawTask } from './types/agent-output.type';

@Injectable()
export class AgentService {
  constructor(private readonly prisma: PrismaService) {}

  async upsertSession(
    chatDto: ChatDto,
    userId: string,
    status = 'active',
    intent?: string,
    aiMessage?: string,
  ) {
    const sessionId = chatDto.thread_id;

    if (!sessionId) {
      throw new BadRequestException('thread_id is required');
    }

    try {
      return await this.prisma.$transaction(async (tx) => {
        // Optional validation
        const userExists = await tx.user.findUnique({
          where: { id: userId },
          select: { id: true },
        });

        if (!userExists) {
          throw new BadRequestException('User not found');
        }

        await tx.session.upsert({
          where: {
            id: sessionId,
          },
          create: {
            id: sessionId,
            userId,
            status,
            latestIntent: intent,
          },
          update: {
            status,
            latestIntent: intent,
          },
        });

        const messages: Prisma.MessageCreateManyInput[] = [];

        if (chatDto.message) {
          messages.push({
            sessionId,
            role: 'user',
            content: chatDto.message,
          });
        }

        if (aiMessage) {
          messages.push({
            sessionId,
            role: 'system',
            content: aiMessage,
          });
        }

        if (messages.length > 0) {
          await tx.message.createMany({
            data: messages,
          });
        }

        await tx.message.createMany({
          data: messages,
        });

        return {
          threadId: sessionId,
          status: 'accepted',
        };
      });
    } catch (error: unknown) {
      if (error instanceof Prisma.PrismaClientKnownRequestError) {
        switch (error.code) {
          case 'P2003':
            throw new BadRequestException('Invalid foreign key reference');

          case 'P2025':
            throw new NotFoundException('Referenced data not found');
        }
      }

      if (error instanceof Error) {
        throw new InternalServerErrorException(error.message);
      }

      throw new InternalServerErrorException('Unknown server error');
    }
  }

  async upsertRawTask(userId: string, rawTasks: RawTask[]) {
    if (!userId || !rawTasks?.length) {
      throw new BadRequestException('user_id and raw_tasks is required');
    }

    try {
      return await this.prisma.$transaction(async (tx) => {
        // Validasi user sekali aja
        const user = await tx.user.findUnique({
          where: { id: userId },
          select: { id: true },
        });

        if (!user) {
          throw new BadRequestException('User not found');
        }

        // Parallel upsert semua task
        await Promise.all(
          rawTasks.map((rt) =>
            tx.task.upsert({
              where: {
                id: rt.task_id,
              },
              update: {
                title: rt.title,
                description: rt.description,
                category: rt.category,
                rawInput: rt.raw_input,
                rawTime: rt.raw_time,
              },
              create: {
                id: rt.task_id,
                userId,
                title: rt.title,
                description: rt.description,
                category: rt.category,
                rawInput: rt.raw_input,
                rawTime: rt.raw_time,
              },
            }),
          ),
        );

        return {
          status: 'success',
          total: rawTasks.length,
        };
      });
    } catch (error: unknown) {
      if (error instanceof Prisma.PrismaClientKnownRequestError) {
        switch (error.code) {
          case 'P2003':
            throw new BadRequestException('Invalid foreign key reference');

          case 'P2002':
            throw new ConflictException('Duplicate task detected');
        }
      }

      if (error instanceof Error) {
        throw new InternalServerErrorException(error.message);
      }

      throw new InternalServerErrorException('Unknown server error');
    }
  }

  findAll() {
    return `This action returns all agent`;
  }

  findOne(id: number) {
    return `This action returns a #${id} agent`;
  }

  update(id: number) {
    return `This action updates a #${id} agent`;
  }

  remove(id: number) {
    return `This action removes a #${id} agent`;
  }
}
