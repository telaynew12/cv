import { Body, Controller, Delete, Get, Param, Post, Request, UseGuards } from '@nestjs/common';
import { CoverLetterService } from './cover-letter.service';
import { SaveCoverLetterDto } from './dto/save-cover-letter.dto';
import { OptionalJwtAuthGuard } from '../auth/jwt-auth.guard';

@Controller('cover-letter')
export class CoverLetterController {
  constructor(private readonly coverLetterService: CoverLetterService) {}

  @UseGuards(OptionalJwtAuthGuard)
  @Post('save')
  async saveCoverLetter(@Request() req: any, @Body() dto: SaveCoverLetterDto) {
    const userId = req.user?.id || req.headers['x-user-id'] || dto.userId || 'guest';
    const saved = await this.coverLetterService.save(userId, dto);
    return {
      success: true,
      message: 'Cover letter saved successfully to MongoDB',
      document: saved,
    };
  }

  @UseGuards(OptionalJwtAuthGuard)
  @Get()
  async getLatestCoverLetter(@Request() req: any) {
    const userId = req.user?.id || req.headers['x-user-id'] || 'guest';
    const document = await this.coverLetterService.findLatestByUser(userId);
    return {
      success: true,
      document,
    };
  }

  @UseGuards(OptionalJwtAuthGuard)
  @Get('all')
  async getAllCoverLetters(@Request() req: any) {
    const userId = req.user?.id || req.headers['x-user-id'] || 'guest';
    const documents = await this.coverLetterService.findAllByUser(userId);
    return {
      success: true,
      documents,
    };
  }

  @UseGuards(OptionalJwtAuthGuard)
  @Get(':id')
  async getCoverLetterById(@Param('id') id: string, @Request() req: any) {
    const userId = req.user?.id || req.headers['x-user-id'];
    const document = await this.coverLetterService.findById(id, userId);
    return {
      success: true,
      document,
    };
  }

  @UseGuards(OptionalJwtAuthGuard)
  @Delete(':id')
  async deleteCoverLetter(@Param('id') id: string, @Request() req: any) {
    const userId = req.user?.id || req.headers['x-user-id'] || 'guest';
    return this.coverLetterService.delete(id, userId);
  }
}

