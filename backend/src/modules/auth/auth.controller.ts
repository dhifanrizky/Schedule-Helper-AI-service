import {
  Res,
  Controller,
  Post,
  Body,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBody, ApiResponse } from '@nestjs/swagger';
import { AuthService } from './auth.service.js';
import { RegisterDto, LoginDto } from './dto/auth.dto.js';
import { UseGuards, Req, Get } from '@nestjs/common';
import { GoogleGuard } from './guard/google.guard.js';
import { Response } from 'express';

@ApiTags('auth')
@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post('register')
  @ApiOperation({ summary: 'Register a new user' })
  @ApiBody({ type: RegisterDto })
  @ApiResponse({ status: 201, description: 'User registered successfully' })
  @ApiResponse({ status: 403, description: 'Email already in use' })
  register(@Body() dto: RegisterDto) {
    return this.authService.register(dto);
  }

  @HttpCode(HttpStatus.OK)
  @Post('login')
  @ApiOperation({ summary: 'Sign in with email and password' })
  @ApiBody({ type: LoginDto })
  @ApiResponse({ status: 200, description: 'Login successful, returns JWT' })
  @ApiResponse({ status: 403, description: 'Invalid credentials' })
  login(@Body() dto: LoginDto) {
    return this.authService.login(dto);
  }

  @HttpCode(HttpStatus.OK)
  @Post('logout')
  @ApiOperation({ summary: 'Logout user' })
  @ApiResponse({ status: 200, description: 'Logout successful' })
  logout() {
    // JWT is stateless on the backend. True logout is clearing the token on the frontend.
    // This endpoint exists to frontend expectations.
    return { message: 'Logged out successfully' };
  }

  @Get('google')
  @UseGuards(GoogleGuard)
  @ApiOperation({ summary: 'Login with Google OAuth2' })
  googleAuth() {
    // This endpoint will redirect the user to the Google login page.
  }

  @Get('google/callback')
  @UseGuards(GoogleGuard)
  @ApiOperation({ summary: 'Google OAuth2 callback URL' })
  async googleAuthRedirect(@Req() req: any, @Res() res: Response) {
    // Tambahkan @Res() res: Response di sini
    const tokenData = await this.authService.googleLogin(req);

    // Asumsikan tokenData mengembalikan object { access_token: "..." }
    const token = tokenData.access_token;

    const frontendUrl = process.env.FRONTEND_URL || 'http://localhost:3001';
    return res.redirect(`${frontendUrl}/auth/callback?token=${token}`);
  }
}
