import { ForbiddenException, Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { JwtService } from '@nestjs/jwt';
import * as argon2 from 'argon2';
import { PrismaService } from '../prisma/prisma.service.js';
import { RegisterDto, LoginDto } from './dto/auth.dto.js';

@Injectable()
export class AuthService {
  constructor(
    private prisma: PrismaService,
    private jwt: JwtService,
    private config: ConfigService,
  ) {}

  async register(dto: RegisterDto) {
    const hash = await argon2.hash(dto.password);

    try {
      const user = await this.prisma.user.create({
        data: {
          email: dto.email,
          hash,
          name: dto.name,
        },
      });

      return this.signToken(user.id, user.email);
    } catch (error) {
      if (
        error &&
        typeof error === 'object' &&
        'code' in error &&
        error.code === 'P2002'
      ) {
        throw new ForbiddenException('Email already in use');
      }
      throw error;
    }
  }

  async login(dto: LoginDto) {
    const user = await this.prisma.user.findUnique({
      where: { email: dto.email },
    });

    if (!user) {
      throw new ForbiddenException('Invalid credentials');
    }

    const passwordValid = await argon2.verify(user.hash, dto.password);

    if (!passwordValid) {
      throw new ForbiddenException('Invalid credentials');
    }

    return this.signToken(user.id, user.email);
  }

  async googleLogin(req: any) {
    if (!req.user) {
      throw new ForbiddenException('No user from google');
    }

    let user = await this.prisma.user.findUnique({
      where: { email: req.user.email },
    });

    if (!user) {
      const dummyHash = await argon2.hash(Math.random().toString(36).substring(7));
      user = await this.prisma.user.create({
        data: {
          email: req.user.email,
          name: req.user.name,
          hash: dummyHash,
          googleAccessToken: req.user.accessToken,
          googleRefreshToken: req.user.refreshToken,
        },
      });
    } else {
      // Update tokens if user already exists
      user = await this.prisma.user.update({
        where: { email: req.user.email },
        data: {
          googleAccessToken: req.user.accessToken,
          googleRefreshToken: req.user.refreshToken || user.googleRefreshToken,
        },
      });
    }

    return this.signToken(user.id, user.email);
  }

  async signToken(
    userId: string,
    email: string,
  ): Promise<{ access_token: string }> {
    const payload = {
      sub: userId,
      email,
    };

    const secret = this.config.get<string>('JWT_SECRET');
    const expiresIn = this.config.get<string>('JWT_EXPIRES_IN') || '1d';

    const token = await this.jwt.signAsync(payload, {
      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
      expiresIn: expiresIn as any,
      secret,
    });

    return { access_token: token };
  }
}
