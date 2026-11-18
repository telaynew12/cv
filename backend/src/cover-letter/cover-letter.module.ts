import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { CoverLetter, CoverLetterSchema } from './schemas/cover-letter.schema';
import { CoverLetterService } from './cover-letter.service';
import { CoverLetterController } from './cover-letter.controller';

@Module({
  imports: [
    MongooseModule.forFeature([{ name: CoverLetter.name, schema: CoverLetterSchema }]),
  ],
  providers: [CoverLetterService],
  controllers: [CoverLetterController],
  exports: [CoverLetterService, MongooseModule],
})
export class CoverLetterModule {}
