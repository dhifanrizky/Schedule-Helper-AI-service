import { ForbiddenException, Injectable } from '@nestjs/common';
import { ChatDto } from './dto/chat.dto';
import { PrismaService } from '../prisma/prisma.service';
import {
  BadRequestException,
  InternalServerErrorException,
} from '@nestjs/common';
import { Prisma } from '../../../generated/prisma/client';
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access */

@Injectable()
export class AgentService {
  constructor(private readonly prisma: PrismaService) {}

  async createSession(chatDto: ChatDto, userId: string) {
    // 1. Kasih default atau validasi agar tidak 'undefined'
    const sessionId = chatDto.thread_id;

    if (!sessionId) {
      throw new BadRequestException('thread_id is required');
    }

    try {
      // eslint-disable-next-line @typescript-eslint/no-unsafe-return
      return await this.prisma.$transaction(async (tx) => {
        // 2. Cek session
        const existingSession = await tx.session.findUnique({
          where: { id: sessionId },
        });
        const user = await tx.user.findFirst({
          where: { id: userId },
        });
        console.log(user);

        if (!existingSession) {
          await tx.session.create({
            data: {
              id: sessionId,
              userId: userId,
              status: 'active',
            },
          });
        }

        // 3. Simpan pesan
        await tx.message.create({
          data: {
            sessionId: sessionId, // Sekarang TS yakin ini string
            role: 'user',
            content: chatDto.message,
          },
        });

        return {
          threadId: sessionId,
          status: 'accepted',
        };
      });
    } catch (error: any) {
      // Pakai :any atau lakukan pengecekan tipe
      // Cek apakah ini error dari Prisma
      console.log(userId);
      if (error instanceof Prisma.PrismaClientKnownRequestError) {
        if (error.code === 'P2003') {
          throw new BadRequestException(
            'User ID tidak valid atau tidak ditemukan di database.',
          );
        }
      }

      // Lempar error asli kalau bukan P2003
      throw new InternalServerErrorException(
        error.message || 'AI Service Error',
      );
    }
  }

  create() {
    return 'This action adds a new agent';
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
