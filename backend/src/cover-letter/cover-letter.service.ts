import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model, isValidObjectId } from 'mongoose';
import { CoverLetter, CoverLetterDocument } from './schemas/cover-letter.schema';
import { SaveCoverLetterDto } from './dto/save-cover-letter.dto';

@Injectable()
export class CoverLetterService {
  constructor(
    @InjectModel(CoverLetter.name) private readonly coverLetterModel: Model<CoverLetterDocument>,
  ) {}

  async save(userId: string, dto: SaveCoverLetterDto): Promise<CoverLetterDocument> {
    const effectiveUserId = userId || dto.userId || 'guest';

    // 1. If explicit id provided and valid, attempt update
    if (dto.id && isValidObjectId(dto.id)) {
      const existing = await this.coverLetterModel.findOne({ _id: dto.id, userId: effectiveUserId }).exec();
      if (existing) {
        Object.assign(existing, {
          title: dto.title ?? existing.title,
          theme: dto.theme ?? existing.theme,
          companyName: dto.companyName ?? existing.companyName,
          jobTitle: dto.jobTitle ?? existing.jobTitle,
          date: dto.date ?? existing.date,
          sender: dto.sender ? { ...existing.sender, ...dto.sender } : existing.sender,
          recipient: dto.recipient ? { ...existing.recipient, ...dto.recipient } : existing.recipient,
          body: dto.body ?? existing.body,
          toggles: dto.toggles ?? existing.toggles,
          rawSnapshot: dto.rawSnapshot ?? existing.rawSnapshot,
        });
        return existing.save();
      }
    }

    // 2. Otherwise update latest document for user if exists and no id was passed
    if (!dto.id && effectiveUserId !== 'guest') {
      const latest = await this.coverLetterModel.findOne({ userId: effectiveUserId, isArchived: false }).sort({ updatedAt: -1 }).exec();
      if (latest) {
        Object.assign(latest, {
          title: dto.title ?? latest.title,
          theme: dto.theme ?? latest.theme,
          companyName: dto.companyName ?? latest.companyName,
          jobTitle: dto.jobTitle ?? latest.jobTitle,
          date: dto.date ?? latest.date,
          sender: dto.sender ? { ...latest.sender, ...dto.sender } : latest.sender,
          recipient: dto.recipient ? { ...latest.recipient, ...dto.recipient } : latest.recipient,
          body: dto.body ?? latest.body,
          toggles: dto.toggles ?? latest.toggles,
          rawSnapshot: dto.rawSnapshot ?? latest.rawSnapshot,
        });
        return latest.save();
      }
    }

    // 3. Create fresh Cover Letter document
    const newDoc = new this.coverLetterModel({
      userId: effectiveUserId,
      title: dto.title || 'Software Developer Cover Letter',
      theme: dto.theme || 'executive',
      companyName: dto.companyName || 'Acme Corporation',
      jobTitle: dto.jobTitle || 'Software Developer',
      date: dto.date || new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }),
      sender: dto.sender || {
        name: 'TELAYNEW AMBACHEW',
        role: 'Full-Stack Developer',
        email: 'telaynew11@gmail.com',
        phone: '+251963391736',
        location: 'Addis Ababa, Ethiopia',
      },
      recipient: dto.recipient || {
        name: 'Hiring Manager',
        title: 'Talent Acquisition Team',
        company: 'Acme Corporation',
        location: 'San Francisco, CA',
      },
      body: dto.body || '',
      toggles: dto.toggles || {},
      rawSnapshot: dto.rawSnapshot || {},
      isArchived: false,
    });

    return newDoc.save();
  }

  async findLatestByUser(userId: string): Promise<CoverLetterDocument | null> {
    return this.coverLetterModel
      .findOne({ userId, isArchived: false })
      .sort({ updatedAt: -1 })
      .exec();
  }

  async findAllByUser(userId: string): Promise<CoverLetterDocument[]> {
    return this.coverLetterModel
      .find({ userId, isArchived: false })
      .sort({ updatedAt: -1 })
      .exec();
  }

  async findById(id: string, userId?: string): Promise<CoverLetterDocument> {
    const query: any = { _id: id };
    if (userId && userId !== 'guest') {
      query.userId = userId;
    }
    const doc = await this.coverLetterModel.findOne(query).exec();
    if (!doc) {
      throw new NotFoundException(`Cover letter with id "${id}" was not found.`);
    }
    return doc;
  }

  async delete(id: string, userId: string): Promise<{ success: boolean; message: string }> {
    const doc = await this.findById(id, userId);
    doc.isArchived = true;
    await doc.save();
    return { success: true, message: 'Cover letter deleted successfully.' };
  }
}
