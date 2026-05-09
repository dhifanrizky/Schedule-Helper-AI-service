import {
  ApiExtraModels,
  ApiProperty,
  ApiPropertyOptional,
  getSchemaPath,
} from '@nestjs/swagger';
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
  @ApiProperty({ example: 'Finish report draft' })
  task!: string;

  @IsNumber()
  @ApiProperty({ example: 2 })
  priority!: number;

  @IsString()
  @ApiProperty({ example: '2026-05-10T09:00:00.000Z' })
  deadline!: string;
}

class CounselorApprovedDataDto {
  @IsString()
  @ApiProperty({ example: 'counselor_review' })
  type!: 'counselor_review';

  @IsBoolean()
  @ApiProperty({ example: true })
  approved!: boolean;

  @IsOptional()
  @IsString()
  @ApiPropertyOptional({ example: 'Revised draft text.' })
  additional_context?: string | null;
}

class PrioritizerApprovedDataDto {
  @IsString()
  @ApiProperty({ example: 'prioritizer_review' })
  type!: 'prioritizer_review';

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => PrioritizedTaskDto)
  @ApiProperty({ type: [PrioritizedTaskDto] })
  tasks!: PrioritizedTaskDto[];
}

@ApiExtraModels(CounselorApprovedDataDto, PrioritizerApprovedDataDto)
export class ChatDto {
  @IsOptional()
  @IsString()
  @ApiPropertyOptional({
    description:
      'Required when resuming a session. Must be provided if sending approved_data.',
  })
  thread_id?: string;

  @IsOptional()
  @ApiPropertyOptional({
    description:
      'Only for resume flow. Requires thread_id. Send counselor_review or prioritizer_review payload.',
    oneOf: [
      { $ref: getSchemaPath(CounselorApprovedDataDto) },
      { $ref: getSchemaPath(PrioritizerApprovedDataDto) },
    ],
  })
  approved_data?: CounselorApprovedDataDto | PrioritizerApprovedDataDto;

  @IsOptional()
  @IsString()
  @ApiProperty({ example: 'Aduh aku lagi pusing banget tapi banyak tugas' })
  message?: string;
}
