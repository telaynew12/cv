import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Schema as MongooseSchema } from 'mongoose';

export type CvDocument = Cv & Document;

@Schema({ _id: false })
export class ContactItem {
  @Prop({ default: 'fas fa-link' })
  icon: string;

  @Prop({ default: '' })
  val: string;
}

@Schema({ _id: false })
export class SectionItem {
  @Prop({ default: '' })
  title: string;

  @Prop({ default: '' })
  date: string;

  @Prop({ default: '' })
  sub: string;

  @Prop({ type: [String], default: [] })
  bullets: string[];
}

@Schema({ _id: false })
export class SectionData {
  @Prop({ required: true })
  id: string;

  @Prop({ default: 'SECTION' })
  title: string;

  @Prop({ default: 1 })
  order: number;

  @Prop({ default: 'main' })
  col: string;

  @Prop({ type: [SectionItem], default: [] })
  items: SectionItem[];
}

@Schema({ _id: false })
export class PhotoConfig {
  @Prop({ default: '' })
  photo: string;

  @Prop({ default: true })
  showPhoto: boolean;

  @Prop({ default: 'center' })
  photoAlign: string;

  @Prop({ default: 'circle' })
  photoShape: string;
}

@Schema({ timestamps: true, collection: 'cvs' })
export class Cv {
  @Prop({ required: true, index: true })
  userId: string;

  @Prop({ default: 'Telaynew Ambachew - CV', trim: true })
  title: string;

  @Prop({ default: 'TELAYNEW AMBACHEW' })
  name: string;

  @Prop({ default: 'Full-Stack Developer' })
  job: string;

  @Prop({ default: 'modern' })
  template: string;

  @Prop({ type: [ContactItem], default: [] })
  contacts: ContactItem[];

  @Prop({ type: [SectionData], default: [] })
  sections: SectionData[];

  @Prop({ type: PhotoConfig, default: () => ({}) })
  photoConfig: PhotoConfig;

  @Prop({ type: MongooseSchema.Types.Mixed, default: {} })
  rawSnapshot: Record<string, any>;

  @Prop({ default: false })
  isDefault: boolean;

  @Prop({ default: false })
  isArchived: boolean;
}

export const CvSchema = SchemaFactory.createForClass(Cv);

// Indexes
CvSchema.index({ userId: 1, updatedAt: -1 });
CvSchema.index({ userId: 1, title: 1 });
CvSchema.index({ createdAt: -1 });
