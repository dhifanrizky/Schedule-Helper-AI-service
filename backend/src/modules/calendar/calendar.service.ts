import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service.js';
import { CreateCalendarDto, UpdateCalendarDto } from './dto/calendar.dto.js';

@Injectable()
export class CalendarService {
  constructor(private readonly prisma: PrismaService) {}

  async findAll(userId: string) {
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
      },
    });
  }

  async update(id: string, userId: string, dto: UpdateCalendarDto) {
    await this.findOne(id, userId); // Verify existence and ownership

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
    await this.findOne(id, userId); // Verify existence and ownership

    return this.prisma.task.delete({
      where: { id },
    });
  }
}
