import { ApiProperty } from '@nestjs/swagger';
import { IsEmail, IsOptional, IsString } from 'class-validator';

export class EditUserDto {
    @ApiProperty({ example: 'newemail@example.com', required: false })
    @IsEmail()
    @IsOptional()
    email?: string;

    @ApiProperty({ example: 'John', required: false })
    @IsString()
    @IsOptional()
    firstName?: string;

    @ApiProperty({ example: 'Doe', required: false })
    @IsString()
    @IsOptional()
    lastName?: string;
}
