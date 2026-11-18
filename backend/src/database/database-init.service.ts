import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { InjectConnection } from '@nestjs/mongoose';
import { Connection } from 'mongoose';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class DatabaseInitService implements OnModuleInit {
  private readonly logger = new Logger(DatabaseInitService.name);

  constructor(
    @InjectConnection() private readonly connection: Connection,
    private readonly configService: ConfigService,
  ) {}

  async onModuleInit() {
    try {
      const dbName = this.configService.get<string>('database.dbName', 'cvforge');
      const autoSync = this.configService.get<boolean>('database.autoSync', true);

      this.logger.log(`[DatabaseInit] Connected to MongoDB Atlas. Target Database: "${dbName}"`);

      // 1. Ensure required collections exist in the database
      const existingCollections = await this.connection.db.listCollections().toArray();
      const existingNames = new Set(existingCollections.map((c) => c.name));

      const requiredCollections = ['users', 'cvs', 'cover_letters'];
      for (const col of requiredCollections) {
        if (!existingNames.has(col)) {
          this.logger.log(`[DatabaseInit] Collection "${col}" not found. Creating collection...`);
          await this.connection.db.createCollection(col);
          this.logger.log(`[DatabaseInit] Collection "${col}" created successfully.`);
        } else {
          this.logger.log(`[DatabaseInit] Collection "${col}" verified.`);
        }
      }

      // 2. Auto-sync schema and indexes if configured (DB_AUTO_SYNC=true or UPDATE_SCHEMA_ON_CHANGE=true)
      if (autoSync) {
        this.logger.log('[DatabaseInit] DB_AUTO_SYNC is enabled. Synchronizing schemas and collection indexes...');
        const registeredModelNames = Object.keys(this.connection.models);
        for (const modelName of registeredModelNames) {
          const model = this.connection.models[modelName];
          if (model && typeof model.syncIndexes === 'function') {
            await model.syncIndexes();
            this.logger.log(`[DatabaseInit] Synced indexes for model: ${modelName}`);
          }
        }
        this.logger.log('[DatabaseInit] All schemas and database collections are up to date.');
      } else {
        this.logger.log('[DatabaseInit] DB_AUTO_SYNC is disabled. Schema changes sync bypassed.');
      }
    } catch (err) {
      this.logger.error(`[DatabaseInit] Failed to initialize collections or sync schemas: ${err.message}`, err.stack);
    }
  }
}
