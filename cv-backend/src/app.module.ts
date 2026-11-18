import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import configuration from './config/configuration';
import { DatabaseModule } from './database/database.module';
import { UsersModule } from './users/users.module';
import { AuthModule } from './auth/auth.module';
import { CvModule } from './cv/cv.module';
import { CoverLetterModule } from './cover-letter/cover-letter.module';
import { DocumentsModule } from './documents/documents.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      load: [configuration],
      envFilePath: ['.env', '../.env'],
    }),
    DatabaseModule,
    UsersModule,
    AuthModule,
    CvModule,
    CoverLetterModule,
    DocumentsModule,
  ],
})
export class AppModule {}

