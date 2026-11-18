import { Injectable } from '@nestjs/common';
import { CvService } from '../cv/cv.service';
import { CoverLetterService } from '../cover-letter/cover-letter.service';

@Injectable()
export class DocumentsService {
  constructor(
    private readonly cvService: CvService,
    private readonly coverLetterService: CoverLetterService,
  ) {}

  async getUserDocuments(userId: string) {
    const effectiveUserId = userId || 'guest';
    const [cvs, coverLetters] = await Promise.all([
      this.cvService.findAllByUser(effectiveUserId),
      this.coverLetterService.findAllByUser(effectiveUserId),
    ]);

    const formattedCvs = cvs.map((doc: any) => ({
      id: doc._id.toString(),
      type: 'cv',
      title: doc.title || `${doc.name || 'Candidate'} - CV`,
      subtitle: `${doc.name} • ${doc.job || 'Full-Stack Developer'}`,
      badge: 'CV / Resume',
      template: doc.template || 'modern',
      updatedAt: doc.updatedAt,
      createdAt: doc.createdAt,
      data: doc,
    }));

    const formattedCls = coverLetters.map((doc: any) => ({
      id: doc._id.toString(),
      type: 'cover-letter',
      title: doc.title || 'Cover Letter',
      subtitle: `${doc.companyName || 'Company'} • ${doc.jobTitle || 'Role'}`,
      badge: 'Cover Letter',
      theme: doc.theme || 'executive',
      updatedAt: doc.updatedAt,
      createdAt: doc.createdAt,
      data: doc,
    }));

    // Combine and sort by newest updated
    const all = [...formattedCvs, ...formattedCls].sort(
      (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
    );

    return {
      success: true,
      count: all.length,
      cvCount: formattedCvs.length,
      coverLetterCount: formattedCls.length,
      documents: all,
    };
  }
}

