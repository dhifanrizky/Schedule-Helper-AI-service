import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import {
  IsString,
  IsNotEmpty,
  IsOptional,
  IsNumber,
  IsDateString,
} from 'class-validator';

export class CreateCalendarDto {
  @ApiProperty({ example: 'Meeting with Team' })
  @IsString()
  @IsNotEmpty()
  title!: string;

  @ApiProperty({ example: 'Discuss project architecture' })
  @IsString()
  @IsNotEmpty()
  description!: string;

  @ApiProperty({ example: 'serius' })
  @IsString()
  @IsNotEmpty()
  category!: string;

  @ApiPropertyOptional({ example: 60 })
  @IsNumber()
  @IsOptional()
  estimatedMinutes?: number;

  @ApiPropertyOptional({ example: 1 })
  @IsNumber()
  @IsOptional()
  priority?: number;

  @ApiPropertyOptional({ example: '2026-05-10T10:00:00Z' })
  @IsDateString()
  @IsOptional()
  deadline?: string;

  @ApiPropertyOptional({ example: '2026-05-06T09:00:00Z' })
  @IsDateString()
  @IsOptional()
  startTime?: string;

  @ApiPropertyOptional({ example: 'pending' })
  @IsString()
  @IsOptional()
  status?: string;
}

export class UpdateCalendarDto {
  @ApiPropertyOptional({ example: 'Updated Meeting Title' })
  @IsString()
  @IsOptional()
  title?: string;

  @ApiPropertyOptional()
  @IsString()
  @IsOptional()
  description?: string;

  @ApiPropertyOptional()
  @IsString()
  @IsOptional()
  category?: string;

  @ApiPropertyOptional()
  @IsNumber()
  @IsOptional()
  estimatedMinutes?: number;

  @ApiPropertyOptional()
  @IsNumber()
  @IsOptional()
  priority?: number;

  @ApiPropertyOptional()
  @IsDateString()
  @IsOptional()
  deadline?: string;

  @ApiPropertyOptional()
  @IsDateString()
  @IsOptional()
  startTime?: string;

  @ApiPropertyOptional({ example: 'completed' })
  @IsString()
  @IsOptional()
  status?: string;
}
