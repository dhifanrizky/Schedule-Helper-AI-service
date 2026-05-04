FROM node:18

WORKDIR /app

# Copy file konfigurasi dependency
COPY package*.json ./

# Install semua dependency
RUN npm install

# Copy seluruh kode sumber
COPY . .

# Generate Prisma Client di dalam container
RUN npx prisma generate

# Buka port untuk backend
EXPOSE 3000

# Jalankan server dalam mode development (watch mode)
CMD ["npm", "run", "start:dev"]
