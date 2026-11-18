import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Schema as MongooseSchema } from 'mongoose';

export type CoverLetterDocument = CoverLetter & Document;

@Schema({ _id: false })
export class SenderDetails {
  @Prop({ default: 'TELAYNEW AMBACHEW' })
  name: string;

  @Prop({ default: 'Full-Stack Developer' })
  role: string;

  @Prop({ default: 'telaynew11@gmail.com' })
  email: string;

  @Prop({ default: '+251963391736' })
  phone: string;

  @Prop({ default: 'Addis Ababa, Ethiopia' })
  location: string;
}

@Schema({ _id: false })
export class RecipientDetails {
  @Prop({ default: 'Hiring Manager' })
  name: string;

  @Prop({ default: 'Talent Acquisition Team' })
  title: string;

  @Prop({ default: 'Acme Corporation' })
  company: string;

  @Prop({ default: 'San Francisco, CA' })
  location: string;
}

@Schema({ timestamps: true, collection: 'cover_letters' })
export class CoverLetter {
  @Prop({ required: true, index: true })
  userId: string;

  @Prop({ default: 'Software Developer Cover Letter', trim: true })
  title: string;

  @Prop({ default: 'executive' })
  theme: string;

  @Prop({ default: 'Acme Corporation' })
  companyName: string;

  @Prop({ default: 'Software Developer' })
  jobTitle: string;

  @Prop({ default: '' })
  date: string;

  @Prop({ type: SenderDetails, default: () => ({}) })
  sender: SenderDetails;

  @Prop({ type: RecipientDetails, default: () => ({}) })
  recipient: RecipientDetails;

  @Prop({ default: '' })
  body: string;

  @Prop({ type: MongooseSchema.Types.Mixed, default: {} })
  toggles: Record<string, boolean>;

  @Prop({ type: MongooseSchema.Types.Mixed, default: {} })
  rawSnapshot: Record<string, any>;

  @Prop({ default: false })
  isArchived: boolean;
}

export const CoverLetterSchema = SchemaFactory.createForClass(CoverLetter);

// Indexes
CoverLetterSchema.index({ userId: 1, updatedAt: -1 });
CoverLetterSchema.index({ userId: 1, title: 1 });
CoverLetterSchema.index({ createdAt: -1 });
