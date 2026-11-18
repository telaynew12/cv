import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model, isValidObjectId } from 'mongoose';
import { Cv, CvDocument } from './schemas/cv.schema';
import { SaveCvDto } from './dto/save-cv.dto';

@Injectable()
export class CvService {
  constructor(
    @InjectModel(Cv.name) private readonly cvModel: Model<CvDocument>,
  ) {}

  async save(userId: string, dto: SaveCvDto): Promise<CvDocument> {
    const effectiveUserId = userId || dto.userId || 'guest';

    // 1. If explicit id provided and valid, attempt update
    if (dto.id && isValidObjectId(dto.id)) {
      const existing = await this.cvModel.findOne({ _id: dto.id, userId: effectiveUserId }).exec();
      if (existing) {
        Object.assign(existing, {
          title: dto.title ?? existing.title,
          name: dto.name ?? existing.name,
          job: dto.job ?? existing.job,
          template: dto.template ?? existing.template,
          contacts: dto.contacts ?? existing.contacts,
          sections: dto.sections ?? existing.sections,
          photoConfig: dto.photoConfig ?? existing.photoConfig,
          rawSnapshot: dto.rawSnapshot ?? existing.rawSnapshot,
          isDefault: dto.isDefault ?? existing.isDefault,
        });
        return existing.save();
      }
    }

    // 2. Otherwise update latest document for user if exists and no id was passed, or create new
    if (!dto.id && effectiveUserId !== 'guest') {
      const latest = await this.cvModel.findOne({ userId: effectiveUserId, isArchived: false }).sort({ updatedAt: -1 }).exec();
      if (latest) {
        Object.assign(latest, {
          title: dto.title ?? latest.title,
          name: dto.name ?? latest.name,
          job: dto.job ?? latest.job,
          template: dto.template ?? latest.template,
          contacts: dto.contacts ?? latest.contacts,
          sections: dto.sections ?? latest.sections,
          photoConfig: dto.photoConfig ?? latest.photoConfig,
          rawSnapshot: dto.rawSnapshot ?? latest.rawSnapshot,
        });
        return latest.save();
      }
    }

    // 3. Create fresh CV document
    const newCv = new this.cvModel({
      userId: effectiveUserId,
      title: dto.title || `${dto.name || 'Telaynew Ambachew'} - CV`,
      name: dto.name || 'TELAYNEW AMBACHEW',
      job: dto.job || 'Full-Stack Developer',
      template: dto.template || 'modern',
      contacts: dto.contacts || [],
      sections: dto.sections || [],
      photoConfig: dto.photoConfig || {},
      rawSnapshot: dto.rawSnapshot || {},
      isDefault: dto.isDefault ?? true,
      isArchived: false,
    });

    return newCv.save();
  }

  async findLatestByUser(userId: string): Promise<CvDocument | null> {
    return this.cvModel
      .findOne({ userId, isArchived: false })
      .sort({ updatedAt: -1 })
      .exec();
  }

  async findAllByUser(userId: string): Promise<CvDocument[]> {
    return this.cvModel
      .find({ userId, isArchived: false })
      .sort({ updatedAt: -1 })
      .exec();
  }

  async findById(id: string, userId?: string): Promise<CvDocument> {
    const query: any = { _id: id };
    if (userId && userId !== 'guest') {
      query.userId = userId;
    }
    const cv = await this.cvModel.findOne(query).exec();
    if (!cv) {
      throw new NotFoundException(`CV with id "${id}" was not found.`);
    }
    return cv;
  }

  async delete(id: string, userId: string): Promise<{ success: boolean; message: string }> {
    const cv = await this.findById(id, userId);
    cv.isArchived = true;
    await cv.save();
    return { success: true, message: 'CV deleted successfully.' };
  }
}
