import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

export type UserDocument = User & Document;

@Schema({ timestamps: true, collection: 'users' })
export class User {
  @Prop({ required: true, trim: true })
  name: string;

  @Prop({ required: true, unique: true, lowercase: true, trim: true, index: true })
  email: string;

  @Prop({ required: false, default: '' })
  password?: string;

  @Prop({ required: false, default: null, sparse: true, index: true })
  googleId?: string;

  @Prop({ required: false, default: '' })
  picture?: string;

  @Prop({ default: '' })
  initials: string;

  @Prop({ default: '' })
  avatar: string;

  @Prop({ default: 'user' })
  role: string;

  @Prop({ default: Date.now })
  lastLoginAt: Date;
}

export const UserSchema = SchemaFactory.createForClass(User);

// Explicit compound/single indexes for autoSync
UserSchema.index({ email: 1 }, { unique: true });
UserSchema.index({ googleId: 1 }, { sparse: true });
UserSchema.index({ createdAt: -1 });
