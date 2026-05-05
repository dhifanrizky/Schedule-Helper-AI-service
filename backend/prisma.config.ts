// Memuat file .env secara manual agar Prisma CLI bisa membaca DATABASE_URL
import 'dotenv/config';
import { defineConfig } from 'prisma/config';

export default defineConfig({
  schema: 'prisma/schema.prisma',
  migrations: {
    path: 'prisma/migrations',
  },
  datasource: {
    url:
      process.env['NODE_ENV'] === 'production'
        ? process.env['DATABASE_URL_NEON']
        : process.env['DATABASE_URL'],
  },
});
