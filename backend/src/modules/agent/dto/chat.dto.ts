import { ApiProperty } from '@nestjs/swagger';
import { IsNotEmpty, IsOptional, IsString } from 'class-validator';

export class ChatDto {
  @ApiProperty({ example: 'Aduh aku lagi pusing banget tapi banyak tugas' })
  @IsString()
  @IsNotEmpty()
  message!: string;

  @IsOptional()
  @IsString()
  thread_id?: string;
}
