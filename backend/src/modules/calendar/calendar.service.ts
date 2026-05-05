import { Injectable, NotFoundException, UnauthorizedException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service.js';
import { CreateCalendarDto, UpdateCalendarDto } from './dto/calendar.dto.js';
import { google } from 'googleapis';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class CalendarService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly config: ConfigService,
  ) {}

  private async getGoogleAuth(userId: string) {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
    });

    if (!user || !user.googleAccessToken) {
      return null;
    }

    const oauth2Client = new google.auth.OAuth2(
      this.config.get('GOOGLE_CLIENT_ID'),
      this.config.get('GOOGLE_CLIENT_SECRET'),
      this.config.get('GOOGLE_CALLBACK_URL'),
    );

    oauth2Client.setCredentials({
      access_token: user.googleAccessToken,
      refresh_token: user.googleRefreshToken,
    });

    return google.calendar({ version: 'v3', auth: oauth2Client });
  }

  async findAll(userId: string) {
    // Untuk fitur sinkronisasi tarik (pull), kita tampilkan dari DB lokal
    // Namun kita bisa log data dari google untuk verifikasi
    const calendar = await this.getGoogleAuth(userId);
    if (calendar) {
      try {
        const res = await calendar.events.list({
          calendarId: 'primary',
          timeMin: new Date().toISOString(),
          maxResults: 15,
          singleEvents: true,
          orderBy: 'startTime',
        });
        console.log(`[Google Sync] Berhasil menarik ${res.data.items?.length} event.`);
      } catch (e) {
        console.error('[Google Sync] Gagal menarik data:', e.message);
      }
    }

    return this.prisma.task.findMany({
      where: { userId },
      orderBy: { startTime: 'asc' },
    });
  }

  async findOne(id: string, userId: string) {
    const task = await this.prisma.task.findFirst({
      where: { id, userId },
    });

    if (!task) {
      throw new NotFoundException(`Calendar schedule with ID ${id} not found`);
    }

    return task;
  }

  async create(userId: string, dto: CreateCalendarDto) {
    const calendar = await this.getGoogleAuth(userId);
    let googleEventId: string | null = null;

    if (calendar) {
      try {
        const event = {
          summary: dto.title,
          description: dto.description,
          start: {
            dateTime: dto.startTime ? new Date(dto.startTime).toISOString() : new Date().toISOString(),
            timeZone: 'Asia/Jakarta',
          },
          end: {
            dateTime: dto.deadline ? new Date(dto.deadline).toISOString() : new Date(Date.now() + 3600000).toISOString(),
            timeZone: 'Asia/Jakarta',
          },
        };

        const res = await calendar.events.insert({
          calendarId: 'primary',
          requestBody: event,
        });
        googleEventId = res.data.id;
        console.log('[Google Sync] Event berhasil dibuat:', googleEventId);
      } catch (e) {
        console.error('[Google Sync] Gagal membuat event:', e.message);
      }
    }

    return this.prisma.task.create({
      data: {
        userId,
        title: dto.title,
        description: dto.description,
        category: dto.category,
        estimatedMinutes: dto.estimatedMinutes,
        priority: dto.priority,
        deadline: dto.deadline ? new Date(dto.deadline) : null,
        startTime: dto.startTime ? new Date(dto.startTime) : null,
        status: dto.status || 'pending',
        googleEventId,
      },
    });
  }

  async update(id: string, userId: string, dto: UpdateCalendarDto) {
    const task = await this.findOne(id, userId);
    const calendar = await this.getGoogleAuth(userId);

    if (calendar && task.googleEventId) {
      try {
        await calendar.events.patch({
          calendarId: 'primary',
          eventId: task.googleEventId,
          requestBody: {
            summary: dto.title,
            description: dto.description,
            start: dto.startTime ? { dateTime: new Date(dto.startTime).toISOString() } : undefined,
            end: dto.deadline ? { dateTime: new Date(dto.deadline).toISOString() } : undefined,
          },
        });
      } catch (e) {
        console.error('[Google Sync] Gagal update event:', e.message);
      }
    }

    return this.prisma.task.update({
      where: { id },
      data: {
        title: dto.title,
        description: dto.description,
        category: dto.category,
        estimatedMinutes: dto.estimatedMinutes,
        priority: dto.priority,
        deadline: dto.deadline ? new Date(dto.deadline) : undefined,
        startTime: dto.startTime ? new Date(dto.startTime) : undefined,
        status: dto.status,
      },
    });
  }

  async remove(id: string, userId: string) {
    const task = await this.findOne(id, userId);
    const calendar = await this.getGoogleAuth(userId);

    if (calendar && task.googleEventId) {
      try {
        await calendar.events.delete({
          calendarId: 'primary',
          eventId: task.googleEventId,
        });
      } catch (e) {
        console.error('[Google Sync] Gagal hapus event:', e.message);
      }
    }

    return this.prisma.task.delete({
      where: { id },
    });
  }
}
