import { IsBoolean, IsNotEmpty, IsObject, IsOptional, IsString } from 'class-validator';

export class SaveCoverLetterDto {
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
  theme?: string;

  @IsString()
  @IsOptional()
  companyName?: string;

  @IsString()
  @IsOptional()
  jobTitle?: string;

  @IsString()
  @IsOptional()
  date?: string;

  @IsObject()
  @IsOptional()
  sender?: {
    name?: string;
    role?: string;
    email?: string;
    phone?: string;
    location?: string;
  };

  @IsObject()
  @IsOptional()
  recipient?: {
    name?: string;
    title?: string;
    company?: string;
    location?: string;
  };

  @IsString()
  @IsOptional()
  body?: string;

  @IsObject()
  @IsOptional()
  toggles?: Record<string, boolean>;

  @IsObject()
  @IsOptional()
  rawSnapshot?: Record<string, any>;
}

