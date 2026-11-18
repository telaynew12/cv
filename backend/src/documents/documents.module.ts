import { Module } from '@nestjs/common';
import { DocumentsService } from './documents.service';
import { DocumentsController } from './documents.controller';
import { CvModule } from '../cv/cv.module';
import { CoverLetterModule } from '../cover-letter/cover-letter.module';

@Module({
  imports: [CvModule, CoverLetterModule],
  providers: [DocumentsService],
  controllers: [DocumentsController],
  exports: [DocumentsService],
})
export class DocumentsModule {}
