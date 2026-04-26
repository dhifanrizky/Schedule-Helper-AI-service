import { Controller, Post, Get, Param, Body, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth, ApiResponse } from '@nestjs/swagger';
import { SchedulesService } from './schedules.service.js';
import { JwtGuard } from '../auth/guard/jwt.guard.js';

@ApiTags('schedules')
@ApiBearerAuth()
@UseGuards(JwtGuard)
@Controller('schedules')
export class SchedulesController {
  constructor(private readonly schedulesService: SchedulesService) {}

  @Post('generate')
  @ApiOperation({ summary: 'Generate a new schedule via AI' })
  @ApiResponse({ status: 201, description: 'Schedule generated' })
  generateSchedule(@Body() payload: any) {
    return this.schedulesService.generateSchedule(payload);
  }

  @Get('history')
  @ApiOperation({ summary: 'Get schedule history' })
  @ApiResponse({ status: 200, description: 'Returns schedule history' })
  getHistory() {
    return this.schedulesService.getHistory();
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get schedule details by ID' })
  @ApiResponse({ status: 200, description: 'Returns schedule details' })
  getScheduleById(@Param('id') id: string) {
    return this.schedulesService.getScheduleById(id);
  }
}
