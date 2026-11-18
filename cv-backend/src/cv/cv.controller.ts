import { Body, Controller, Delete, Get, Param, Post, Request, UseGuards } from '@nestjs/common';
import { CvService } from './cv.service';
import { SaveCvDto } from './dto/save-cv.dto';
import { OptionalJwtAuthGuard } from '../auth/jwt-auth.guard';

@Controller('cv')
export class CvController {
  constructor(private readonly cvService: CvService) {}

  @UseGuards(OptionalJwtAuthGuard)
  @Post('save')
  async saveCv(@Request() req: any, @Body() dto: SaveCvDto) {
    const userId = req.user?.id || req.headers['x-user-id'] || dto.userId || 'guest';
    const saved = await this.cvService.save(userId, dto);
    return {
      success: true,
      message: 'CV saved successfully to MongoDB',
      document: saved,
    };
  }

  @UseGuards(OptionalJwtAuthGuard)
  @Get()
  async getLatestCv(@Request() req: any) {
    const userId = req.user?.id || req.headers['x-user-id'] || 'guest';
    const document = await this.cvService.findLatestByUser(userId);
    return {
      success: true,
      document,
    };
  }

  @UseGuards(OptionalJwtAuthGuard)
  @Get('all')
  async getAllCvs(@Request() req: any) {
    const userId = req.user?.id || req.headers['x-user-id'] || 'guest';
    const documents = await this.cvService.findAllByUser(userId);
    return {
      success: true,
      documents,
    };
  }

  @UseGuards(OptionalJwtAuthGuard)
  @Get(':id')
  async getCvById(@Param('id') id: string, @Request() req: any) {
    const userId = req.user?.id || req.headers['x-user-id'];
    const document = await this.cvService.findById(id, userId);
    return {
      success: true,
      document,
    };
  }

  @UseGuards(OptionalJwtAuthGuard)
  @Delete(':id')
  async deleteCv(@Param('id') id: string, @Request() req: any) {
    const userId = req.user?.id || req.headers['x-user-id'] || 'guest';
    return this.cvService.delete(id, userId);
  }
}

