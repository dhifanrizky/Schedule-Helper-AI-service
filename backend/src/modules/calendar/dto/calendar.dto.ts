import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import {
  IsString,
  IsNotEmpty,
  IsOptional,
  IsInt,
  Min,
  IsDateString,
} from 'class-validator';
import { Type } from 'class-transformer';

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
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @IsOptional()
  estimatedMinutes?: number;

  @ApiPropertyOptional({ example: 1 })
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @IsOptional()
  priority?: number;

  @ApiPropertyOptional({ example: '2026-05-10T10:00:00Z' })
  @IsDateString({ strict: false })
  @IsOptional()
  deadline?: string;

  @ApiPropertyOptional({ example: '2026-05-06T09:00:00Z' })
  @IsDateString({ strict: false })
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
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @IsOptional()
  estimatedMinutes?: number;

  @ApiPropertyOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @IsOptional()
  priority?: number;

  @ApiPropertyOptional()
  @IsDateString({ strict: false })
  @IsOptional()
  deadline?: string;

  @ApiPropertyOptional()
  @IsDateString({ strict: false })
  @IsOptional()
  startTime?: string;

  @ApiPropertyOptional({ example: 'completed' })
  @IsString()
  @IsOptional()
  status?: string;
}
