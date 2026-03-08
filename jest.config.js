/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: 'jest-environment-jsdom',
  testMatch: ['**/tests/js/**/*.test.js'],
  // Note: Istanbul cannot instrument code loaded via new Function() / eval,
  // so JS coverage is tracked behaviourally through 46 unit tests rather
  // than via instrumented line coverage.
  collectCoverageFrom: ['static/js/**/*.js'],
};
