import { Controller, Post, Body, HttpCode, HttpStatus } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBody, ApiResponse } from '@nestjs/swagger';
import { AuthService } from './auth.service.js';
import { SignupDto, SigninDto } from './dto/auth.dto.js';

@ApiTags('auth')
@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) { }

  @Post('signup')
  @ApiOperation({ summary: 'Register a new user' })
  @ApiBody({ type: SignupDto })
  @ApiResponse({ status: 201, description: 'User registered successfully' })
  @ApiResponse({ status: 403, description: 'Email already in use' })
  signup(@Body() dto: SignupDto) {
    return this.authService.signup(dto);
  }

  @HttpCode(HttpStatus.OK)
  @Post('signin')
  @ApiOperation({ summary: 'Sign in with email and password' })
  @ApiBody({ type: SigninDto })
  @ApiResponse({ status: 200, description: 'Login successful, returns JWT' })
  @ApiResponse({ status: 403, description: 'Invalid credentials' })
  signin(@Body() dto: SigninDto) {
    return this.authService.signin(dto);
  }
}
