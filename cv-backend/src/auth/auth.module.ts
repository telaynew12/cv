import { Module } from '@nestjs/common';
import { JwtModule } from '@nestjs/jwt';
import { PassportModule } from '@nestjs/passport';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { UsersModule } from '../users/users.module';
import { AuthService } from './auth.service';
import { AuthController } from './auth.controller';
import { JwtStrategy } from './jwt.strategy';
import { JwtAuthGuard, OptionalJwtAuthGuard } from './jwt-auth.guard';

@Module({
  imports: [
    UsersModule,
    PassportModule.register({ defaultStrategy: 'jwt' }),
    JwtModule.registerAsync({
      imports: [ConfigModule],
      useFactory: async (configService: ConfigService) => ({
        secret: configService.get<string>('jwt.secret', 'cvforge_jwt_secret_key_2026_super_secure'),
        signOptions: {
          expiresIn: configService.get<string>('jwt.expiresIn', '7d'),
        },
      }),
      inject: [ConfigService],
    }),
  ],
  providers: [AuthService, JwtStrategy, JwtAuthGuard, OptionalJwtAuthGuard],
  controllers: [AuthController],
  exports: [AuthService, JwtAuthGuard, OptionalJwtAuthGuard, JwtModule],
})
export class AuthModule {}

