import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { DatabaseInitService } from './database-init.service';

@Module({
  imports: [
    MongooseModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: async (configService: ConfigService) => ({
        uri: configService.get<string>('database.uri'),
        dbName: configService.get<string>('database.dbName'),
        autoCreate: true,
        autoIndex: true,
      }),
      inject: [ConfigService],
    }),
  ],
  providers: [DatabaseInitService],
  exports: [MongooseModule, DatabaseInitService],
})
export class DatabaseModule {}

