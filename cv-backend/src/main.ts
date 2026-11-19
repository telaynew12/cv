import { NestFactory } from '@nestjs/core';
import { ValidationPipe, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { AppModule } from './app.module';

async function bootstrap() {
  const logger = new Logger('Bootstrap');
  const app = await NestFactory.create(AppModule);

  const configService = app.get(ConfigService);
  const port = configService.get<number>('port', 3000);
  const corsOrigin = configService.get<string>('corsOrigin', '*');

  // Enable CORS for frontend integration
  app.enableCors({
    origin: corsOrigin === '*' ? true : corsOrigin.split(','),
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'x-user-id'],
  });

  // Global prefix: /api
  app.setGlobalPrefix('api');

  // Global validation pipe
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      transform: true,
      forbidNonWhitelisted: false,
    }),
  );

  await app.listen(port, '0.0.0.0');
  logger.log(`=======================================================`);
  logger.log(`🚀 CVForge NestJS Backend is running on: http://localhost:${port}/api`);
  logger.log(`📦 MongoDB Database: "${configService.get<string>('database.dbName')}"`);
  logger.log(`⚡ Auto-sync Schemas: ${configService.get<boolean>('database.autoSync')}`);
  logger.log(`=======================================================`);
}

bootstrap();

