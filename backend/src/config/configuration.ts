export default () => ({
  port: parseInt(process.env.PORT, 10) || 3000,
  database: {
    uri: process.env.db_url || process.env.DB_URL || 'mongodb+srv://telay:telaynew5870@cluster0.rnebbwt.mongodb.net/',
    dbName: process.env.DB_NAME || 'cvforge',
    autoSync: (process.env.DB_AUTO_SYNC === 'true') || (process.env.UPDATE_SCHEMA_ON_CHANGE === 'true'),
  },
  jwt: {
    secret: process.env.JWT_SECRET || 'cvforge_jwt_secret_key_2026_super_secure',
    expiresIn: process.env.JWT_EXPIRES_IN || '7d',
  },
  corsOrigin: process.env.CORS_ORIGIN || '*',
});
