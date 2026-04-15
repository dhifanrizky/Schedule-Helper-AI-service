import {
  Controller,
  Get,
  Patch,
  Body,
  UseGuards,
} from '@nestjs/common';
import {
  ApiTags,
  ApiOperation,
  ApiBearerAuth,
  ApiResponse,
} from '@nestjs/swagger';
import { UsersService } from './users.service.js';
import { JwtGuard } from '../auth/guard/jwt.guard.js';
import { GetUser } from '../auth/decorator/get-user.decorator.js';
import { EditUserDto } from './dto/edit-user.dto.js';

@ApiTags('users')
@ApiBearerAuth()
@UseGuards(JwtGuard)
@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) { }

  @Get('me')
  @ApiOperation({ summary: 'Get current user profile' })
  @ApiResponse({ status: 200, description: 'Returns the current user' })
  @ApiResponse({ status: 401, description: 'Unauthorized' })
  getMe(@GetUser('id') userId: string) {
    return this.usersService.getMe(userId);
  }

  @Patch()
  @ApiOperation({ summary: 'Update current user profile' })
  @ApiResponse({ status: 200, description: 'User updated successfully' })
  @ApiResponse({ status: 401, description: 'Unauthorized' })
  editUser(@GetUser('id') userId: string, @Body() dto: EditUserDto) {
    return this.usersService.editUser(userId, dto);
  }
}
