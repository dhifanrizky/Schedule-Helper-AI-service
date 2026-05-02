import { ApiProperty } from '@nestjs/swagger';
import { Type } from 'class-transformer';
import {
  IsArray,
  IsBoolean,
  IsNumber,
  IsOptional,
  IsString,
  ValidateNested,
} from 'class-validator';

class PrioritizedTaskDto {
  @IsString()
  task!: string;

  @IsNumber()
  priority!: number;

  @IsString()
  deadline!: string;
}

class CounselorApprovedDataDto {
  @IsString()
  type!: 'counselor_review';

  @IsBoolean()
  approved!: boolean;

  @IsOptional()
  @IsString()
  edited_draft?: string | null;
}

class PrioritizerApprovedDataDto {
  @IsString()
  type!: 'prioritizer_review';

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => PrioritizedTaskDto)
  tasks!: PrioritizedTaskDto[];
}

export class ChatDto {
  @IsOptional()
  @IsString()
  thread_id?: string;

  @IsOptional()
  approved_data?: CounselorApprovedDataDto | PrioritizerApprovedDataDto;

  @IsOptional()
  @IsString()
  @ApiProperty({ example: 'Aduh aku lagi pusing banget tapi banyak tugas' })
  message?: string;
}
