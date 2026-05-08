import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service.js';
import { CreateCalendarDto, UpdateCalendarDto } from './dto/calendar.dto.js';
import { google } from 'googleapis';
import { ConfigService } from '@nestjs/config';

/* eslint-disable
  @typescript-eslint/no-unsafe-assignment
*/
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

    return oauth2Client;
  }

  private async getGoogleCalendar(userId: string) {
    const auth = await this.getGoogleAuth(userId);
    if (!auth) return null;
    return google.calendar({ version: 'v3', auth });
  }

  private async getGoogleTasks(userId: string) {
    const auth = await this.getGoogleAuth(userId);
    if (!auth) return null;
    return google.tasks({ version: 'v1', auth });
  }

  /**
   * Mapping priority ke colorId Google Calendar:
   * 11 = Tomato (merah)  → priority 1 (urgent)
   * 5  = Banana (kuning) → priority 2 (sedang)
   * 2  = Sage (hijau)    → priority 3+ (rendah)
   */
  private getPriorityColor(priority?: number | null): string {
    if (priority === 1) return '11'; // Tomato - merah
    if (priority === 2) return '5'; // Banana - kuning
    return '2'; // Sage - hijau
  }

  async findAll(userId: string) {
    const calendar = await this.getGoogleCalendar(userId);
    if (calendar) {
      try {
        const res = await calendar.events.list({
          calendarId: 'primary',
          timeMin: new Date().toISOString(),
          maxResults: 15,
          singleEvents: true,
          orderBy: 'startTime',
        });
        console.log(
          `[Google Sync] Berhasil menarik ${res.data.items?.length} event.`,
        );
      } catch (e) {
        const message = e instanceof Error ? e.message : String(e);
        console.error('[Google Sync] Gagal menarik data:', message);
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
    const calendar = await this.getGoogleCalendar(userId);
    const tasksClient = await this.getGoogleTasks(userId);
    let googleEventId: string | null = null;
    let googleTaskId: string | null = null;

    // ── 1. Sync ke Google Calendar ──
    if (calendar) {
      try {
        const startDateTime = dto.startTime ?? new Date().toISOString();
        const endDateTime =
          dto.deadline ?? new Date(Date.now() + 3600000).toISOString();

        const event = {
          summary: dto.title,
          description: dto.description,
          start: {
            dateTime: startDateTime,
            timeZone: 'Asia/Jakarta',
          },
          end: {
            dateTime: endDateTime,
            timeZone: 'Asia/Jakarta',
          },
        };

        const res = await calendar.events.insert({
          calendarId: 'primary',
          requestBody: {
            ...event,
            colorId: this.getPriorityColor(dto.priority),
          },
        });
        googleEventId = res.data.id ?? null;
        console.log('[Google Calendar] Event berhasil dibuat:', googleEventId);
      } catch (e) {
        const message = e instanceof Error ? e.message : String(e);
        console.error('[Google Calendar] Gagal membuat event:', message);
      }
    }

    // ── 2. Sync ke Google Tasks (beserta subtasks) ──
    if (tasksClient) {
      try {
        const taskRes = await tasksClient.tasks.insert({
          tasklist: '@default',
          requestBody: {
            title: dto.title,
            notes: dto.description || '',
            due: dto.deadline
              ? new Date(dto.deadline).toISOString()
              : undefined,
          },
        });
        googleTaskId = taskRes.data.id ?? null;
        console.log('[Google Tasks] Task berhasil dibuat:', googleTaskId);

        // Buat subtasks sebagai child task
        if (dto.subtasks && dto.subtasks.length > 0 && googleTaskId) {
          for (const subtask of dto.subtasks) {
            await tasksClient.tasks.insert({
              tasklist: '@default',
              parent: googleTaskId,
              requestBody: { title: subtask },
            });
          }
          console.log(
            `[Google Tasks] ${dto.subtasks.length} subtask berhasil dibuat.`,
          );
        }
      } catch (e) {
        const message = e instanceof Error ? e.message : String(e);
        console.error('[Google Tasks] Gagal membuat task:', message);
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
        googleTaskId,
        subtasks: dto.subtasks,
      },
    });
  }

  async update(id: string, userId: string, dto: UpdateCalendarDto) {
    const task = await this.findOne(id, userId);
    const calendar = await this.getGoogleCalendar(userId);

    if (calendar && task.googleEventId) {
      try {
        await calendar.events.patch({
          calendarId: 'primary',
          eventId: task.googleEventId,
          requestBody: {
            summary: dto.title,
            description: dto.description,
            start: dto.startTime
              ? { dateTime: new Date(dto.startTime).toISOString() }
              : undefined,
            end: dto.deadline
              ? { dateTime: new Date(dto.deadline).toISOString() }
              : undefined,
          },
        });
      } catch (e) {
        const message = e instanceof Error ? e.message : String(e);
        console.error('[Google Calendar] Gagal update event:', message);
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
        subtasks: dto.subtasks,
      },
    });
  }

  async remove(id: string, userId: string) {
    const task = await this.findOne(id, userId);
    const calendar = await this.getGoogleCalendar(userId);
    const tasksClient = await this.getGoogleTasks(userId);

    if (calendar && task.googleEventId) {
      try {
        await calendar.events.delete({
          calendarId: 'primary',
          eventId: task.googleEventId,
        });
        console.log('[Google Calendar] Event berhasil dihapus.');
      } catch (e) {
        const message = e instanceof Error ? e.message : String(e);
        console.error('[Google Calendar] Gagal hapus event:', message);
      }
    }

    if (tasksClient && task.googleTaskId) {
      try {
        await tasksClient.tasks.delete({
          tasklist: '@default',
          task: task.googleTaskId,
        });
        console.log('[Google Tasks] Task berhasil dihapus:', task.googleTaskId);
      } catch (e) {
        const message = e instanceof Error ? e.message : String(e);
        console.error('[Google Tasks] Gagal hapus task:', message);
      }
    }

    return this.prisma.task.delete({
      where: { id },
    });
  }
}
