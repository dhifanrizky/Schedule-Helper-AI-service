import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { PassportStrategy } from '@nestjs/passport';
import { Strategy, VerifyCallback } from 'passport-google-oauth20';

@Injectable()
export class GoogleStrategy extends PassportStrategy(Strategy, 'google') {
  constructor(config: ConfigService) {
    super({
      clientID: config.get<string>('GOOGLE_CLIENT_ID') || 'placeholder-client-id',
      clientSecret: config.get<string>('GOOGLE_CLIENT_SECRET') || 'placeholder-client-secret',
      callbackURL: config.get<string>('GOOGLE_CALLBACK_URL') || 'http://localhost:3000/api/auth/google/callback',
      scope: ['email', 'profile'],
      // Uncomment nanti kalau butuh refresh token untuk Google Calendar API
      // accessType: 'offline',
      // prompt: 'consent',
    });
  }

  async validate(
    accessToken: string,
    refreshToken: string,
    profile: any,
    done: VerifyCallback,
  ): Promise<any> {
    const { name, emails, id } = profile;
    const user = {
      email: emails[0].value,
      name: `${name.givenName} ${name.familyName || ''}`.trim(),
      googleId: id,
      accessToken,
      refreshToken,
    };
    done(null, user);
  }
}
