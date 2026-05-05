import {
  Controller,
  Get,
  Post,
  Body,
  Patch,
  Param,
  Delete,
  UseGuards,
} from '@nestjs/common';
import {
  ApiBearerAuth,
  ApiOperation,
  ApiTags,
  ApiResponse,
} from '@nestjs/swagger';
import { CalendarService } from './calendar.service.js';
import { CreateCalendarDto, UpdateCalendarDto } from './dto/calendar.dto.js';
import { JwtGuard } from '../auth/guard/jwt.guard.js';
import { GetUser } from '../auth/decorator/get-user.decorator.js';

@ApiTags('calendar')
@ApiBearerAuth()
@UseGuards(JwtGuard)
@Controller('calendar')
export class CalendarController {
  constructor(private readonly calendarService: CalendarService) {}

  @Get()
  @ApiOperation({
    summary: 'Synchronize / Pull all calendar schedules for the current user',
  })
  @ApiResponse({ status: 200, description: 'Return all schedules' })
  findAll(@GetUser('id') userId: string) {
    return this.calendarService.findAll(userId);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get a specific schedule by ID' })
  findOne(@Param('id') id: string, @GetUser('id') userId: string) {
    return this.calendarService.findOne(id, userId);
  }

  @Post()
  @ApiOperation({ summary: 'Create a new manual schedule' })
  create(
    @GetUser('id') userId: string,
    @Body() createCalendarDto: CreateCalendarDto,
  ) {
    return this.calendarService.create(userId, createCalendarDto);
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Update an existing schedule' })
  update(
    @Param('id') id: string,
    @GetUser('id') userId: string,
    @Body() updateCalendarDto: UpdateCalendarDto,
  ) {
    return this.calendarService.update(id, userId, updateCalendarDto);
  }

  @Delete(':id')
  @ApiOperation({ summary: 'Delete a schedule' })
  remove(@Param('id') id: string, @GetUser('id') userId: string) {
    return this.calendarService.remove(id, userId);
  }
}
