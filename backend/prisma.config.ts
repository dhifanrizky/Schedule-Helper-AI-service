// Reads from process.env; the CI pipeline should inject required env vars.
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
