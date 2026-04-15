import { Injectable, OnModuleDestroy, OnModuleInit } from '@nestjs/common';
// @ts-ignore - Prisma generated client path
import { PrismaClient } from '../../generated/prisma/client';

@Injectable()
export class PrismaService
  extends PrismaClient
  implements OnModuleInit, OnModuleDestroy {
  constructor() {
    const databaseUrl = process.env.DATABASE_URL;

    if (!databaseUrl) {
      throw new Error('DATABASE_URL is not defined');
    }

    super({
      datasources: {
        db: {
          url: databaseUrl,
        },
      },
    });
  }

  async onModuleInit() {
    await this.$connect();
  }

  async onModuleDestroy() {
    await this.$disconnect();
  }

  cleanDatabase() {
    return this.$transaction([this.user.deleteMany()]);
  }
}
