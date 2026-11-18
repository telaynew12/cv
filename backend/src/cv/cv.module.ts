import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { Cv, CvSchema } from './schemas/cv.schema';
import { CvService } from './cv.service';
import { CvController } from './cv.controller';

@Module({
  imports: [
    MongooseModule.forFeature([{ name: Cv.name, schema: CvSchema }]),
  ],
  providers: [CvService],
  controllers: [CvController],
  exports: [CvService, MongooseModule],
})
export class CvModule {}
