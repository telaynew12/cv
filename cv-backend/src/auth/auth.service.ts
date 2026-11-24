import {
  Injectable,
  ConflictException,
  UnauthorizedException,
} from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import * as bcrypt from 'bcrypt';
import { OAuth2Client } from 'google-auth-library';
import { UsersService } from '../users/users.service';
import { RegisterDto } from './dto/register.dto';
import { LoginDto } from './dto/login.dto';
import { GoogleAuthDto } from './dto/google-auth.dto';

@Injectable()
export class AuthService {
  private googleClient: OAuth2Client;

  constructor(
    private readonly usersService: UsersService,
    private readonly jwtService: JwtService,
    private readonly configService: ConfigService,
  ) {
    const clientId =
      this.configService.get<string>('GOOGLE_CLIENT_ID') ||
      process.env.GOOGLE_CLIENT_ID ||
      '';
    this.googleClient = new OAuth2Client(clientId);
  }

  private computeInitials(name: string): string {
    return name
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() || '')
      .join('');
  }

  async register(registerDto: RegisterDto) {
    const existing = await this.usersService.findByEmail(registerDto.email);
    if (existing) {
      throw new ConflictException('An account with this email address already exists.');
    }

    const saltRounds = 10;
    const hashedPassword = await bcrypt.hash(registerDto.password, saltRounds);
    const initials = this.computeInitials(registerDto.name);

    const user = await this.usersService.create({
      name: registerDto.name.trim(),
      email: registerDto.email.toLowerCase().trim(),
      password: hashedPassword,
      initials,
    });

    const token = this.jwtService.sign({
      sub: user._id.toString(),
      email: user.email,
      name: user.name,
    });

    return {
      message: 'Account created successfully',
      access_token: token,
      token,
      user: {
        id: user._id.toString(),
        name: user.name,
        email: user.email,
        initials: user.initials,
        role: user.role,
      },
    };
  }

  async login(loginDto: LoginDto) {
    const user = await this.usersService.findByEmail(loginDto.email);
    if (!user) {
      throw new UnauthorizedException('Invalid email or password credentials.');
    }

    if (!user.password) {
      throw new UnauthorizedException(
        'This account was created using Google Sign-In. Please click "Continue with Google".',
      );
    }

    const isMatch = await bcrypt.compare(loginDto.password, user.password);
    if (!isMatch) {
      throw new UnauthorizedException('Invalid email or password credentials.');
    }

    await this.usersService.updateLastLogin(user._id.toString());

    const token = this.jwtService.sign({
      sub: user._id.toString(),
      email: user.email,
      name: user.name,
    });

    return {
      message: 'Logged in successfully',
      access_token: token,
      token,
      user: {
        id: user._id.toString(),
        name: user.name,
        email: user.email,
        initials: user.initials,
        picture: user.picture || user.avatar,
        avatar: user.avatar || user.picture,
        role: user.role,
      },
    };
  }

  async authenticateWithGoogle(googleAuthDto: GoogleAuthDto | string) {
    const idToken =
      typeof googleAuthDto === 'string'
        ? googleAuthDto
        : googleAuthDto?.idToken;
    const accessToken =
      typeof googleAuthDto === 'object'
        ? googleAuthDto?.accessToken
        : undefined;

    if (!idToken && !accessToken) {
      throw new UnauthorizedException('Google ID token or access token is required');
    }

    let payload: any;

    if (idToken) {
      const clientId =
        this.configService.get<string>('GOOGLE_CLIENT_ID') ||
        process.env.GOOGLE_CLIENT_ID ||
        '';

      try {
        const ticket = await this.googleClient.verifyIdToken({
          idToken,
          audience: clientId || undefined,
        });
        payload = ticket.getPayload();
      } catch (err: any) {
        throw new UnauthorizedException(
          `Invalid Google ID token: ${err.message || 'Verification failed'}`,
        );
      }
    } else if (accessToken) {
      try {
        const res = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
          headers: { Authorization: `Bearer ${accessToken}` },
        });
        if (!res.ok) {
          throw new Error(`Google returned status ${res.status}`);
        }
        payload = await res.json();
      } catch (err: any) {
        throw new UnauthorizedException(
          `Invalid Google access token: ${err.message || 'Verification failed'}`,
        );
      }
    }

    if (!payload || !payload.email) {
      throw new UnauthorizedException(
        'Google profile does not contain a verified email address.',
      );
    }

    const googleId = payload.sub;
    const email = payload.email.toLowerCase().trim();
    const name = payload.name || payload.email.split('@')[0];
    const picture = payload.picture || '';

    // 1. Look up user by googleId
    let user = await this.usersService.findByGoogleId(googleId);

    // 2. If not found by googleId, look up by email to link account
    if (!user) {
      user = await this.usersService.findByEmail(email);
      if (user) {
        user = await this.usersService.updateGoogleId(
          user._id.toString(),
          googleId,
          picture,
        );
      } else {
        // 3. Create brand-new user (Sign Up)
        const initials = this.computeInitials(name);
        user = await this.usersService.create({
          name,
          email,
          password: '',
          googleId,
          picture,
          avatar: picture,
          initials,
        });
      }
    } else if (picture && (!user.picture || !user.avatar)) {
      user = await this.usersService.updateGoogleId(
        user._id.toString(),
        googleId,
        picture,
      );
    }

    if (!user) {
      throw new UnauthorizedException('Failed to process Google authentication.');
    }

    await this.usersService.updateLastLogin(user._id.toString());

    const token = this.jwtService.sign({
      sub: user._id.toString(),
      email: user.email,
      name: user.name,
    });

    return {
      message: 'Authenticated with Google successfully',
      access_token: token,
      token,
      user: {
        id: user._id.toString(),
        name: user.name,
        email: user.email,
        initials: user.initials,
        picture: user.picture || user.avatar,
        avatar: user.avatar || user.picture,
        role: user.role,
      },
    };
  }
}
