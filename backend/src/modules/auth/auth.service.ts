import { ForbiddenException, Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { JwtService } from '@nestjs/jwt';
import * as argon2 from 'argon2';
import { PrismaService } from '../prisma/prisma.service.js';
import { SignupDto, SigninDto } from './dto/auth.dto.js';

@Injectable()
export class AuthService {
  constructor(
    private prisma: PrismaService,
    private jwt: JwtService,
    private config: ConfigService,
  ) { }

  async signup(dto: SignupDto) {
    // Hash the password
    const hash = await argon2.hash(dto.password);

    try {
      // Save user to database
      const user = await this.prisma.user.create({
        data: {
          email: dto.email,
          hash,
          firstName: dto.firstName,
          lastName: dto.lastName,
        },
      });

      return this.signToken(user.id, user.email);
    } catch (error) {
      // Handle unique constraint violation (duplicate email)
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

  async signin(dto: SigninDto) {
    // Find user by email
    const user = await this.prisma.user.findUnique({
      where: { email: dto.email },
    });

    // If user not found, throw error
    if (!user) {
      throw new ForbiddenException('Invalid credentials');
    }

    // Verify password
    const passwordValid = await argon2.verify(user.hash, dto.password);

    if (!passwordValid) {
      throw new ForbiddenException('Invalid credentials');
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
      expiresIn: expiresIn as any,
      secret,
    });

    return { access_token: token };
  }
}
