/* eslint-disable @typescript-eslint/no-require-imports */
const nextJest = require('next/jest.js');
 
const createJestConfig = nextJest({
  dir: './',
});
 
const config = {
  coverageProvider: 'v8',
  testEnvironment: 'jsdom',
  testMatch: ['<rootDir>/src/**/*.test.{ts,tsx}'],
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  }
};
 
module.exports = createJestConfig(config);
