import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service.js';
import { EditUserDto } from './dto/edit-user.dto.js';

@Injectable()
export class UsersService {
  constructor(private prisma: PrismaService) {}

  async getMe(userId: number) {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
    });

    if (!user) {
      throw new NotFoundException('User not found');
    }

    // Remove hash before returning
    const { hash, ...userWithoutHash } = user;
    return userWithoutHash;
  }

  async editUser(userId: number, dto: EditUserDto) {
    const user = await this.prisma.user.update({
      where: { id: userId },
      data: { ...dto },
    });

    // Remove hash before returning
    const { hash, ...userWithoutHash } = user;
    return userWithoutHash;
  }
}
