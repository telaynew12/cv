import { IsArray, IsBoolean, IsNotEmpty, IsObject, IsOptional, IsString } from 'class-validator';

export class SaveCvDto {
  @IsString()
  @IsOptional()
  id?: string;

  @IsString()
  @IsOptional()
  userId?: string;

  @IsString()
  @IsOptional()
  title?: string;

  @IsString()
  @IsOptional()
  name?: string;

  @IsString()
  @IsOptional()
  job?: string;

  @IsString()
  @IsOptional()
  template?: string;

  @IsArray()
  @IsOptional()
  contacts?: any[];

  @IsArray()
  @IsOptional()
  sections?: any[];

  @IsObject()
  @IsOptional()
  photoConfig?: Record<string, any>;

  @IsObject()
  @IsOptional()
  rawSnapshot?: Record<string, any>;

  @IsBoolean()
  @IsOptional()
  isDefault?: boolean;
}
