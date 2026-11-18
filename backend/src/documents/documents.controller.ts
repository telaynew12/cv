import { Controller, Get, Request, UseGuards } from '@nestjs/common';
import { DocumentsService } from './documents.service';
import { OptionalJwtAuthGuard } from '../auth/jwt-auth.guard';

@Controller('documents')
export class DocumentsController {
  constructor(private readonly documentsService: DocumentsService) {}

  @UseGuards(OptionalJwtAuthGuard)
  @Get()
  async getDocuments(@Request() req: any) {
    const userId = req.user?.id || req.headers['x-user-id'] || 'guest';
    return this.documentsService.getUserDocuments(userId);
  }
}
