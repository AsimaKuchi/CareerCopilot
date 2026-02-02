/**
 * Report Generator for AutoFill Bot
 * 
 * Generates and saves fill reports.
 */

const fs = require('fs');
const path = require('path');

/**
 * Generate a human-readable report
 */
function generateReport(report) {
  const lines = [];
  
  lines.push('═══════════════════════════════════════════════════════════');
  lines.push('  AUTOFILL BOT REPORT');
  lines.push('═══════════════════════════════════════════════════════════');
  lines.push('');
  lines.push(`Application ID: ${report.applicationId}`);
  lines.push(`Started: ${report.startedAt}`);
  lines.push(`Duration: ${(report.duration / 1000).toFixed(2)}s`);
  lines.push(`Status: ${report.status.toUpperCase()}`);
  lines.push('');
  lines.push(`ATS Type: ${report.atsType} (confidence: ${report.atsConfidence})`);
  lines.push('');
  
  // Filled fields
  lines.push('───────────────────────────────────────────────────────────');
  lines.push(`  FILLED FIELDS (${report.filledFields.length})`);
  lines.push('───────────────────────────────────────────────────────────');
  for (const field of report.filledFields) {
    const value = field.value?.length > 50 ? field.value.substring(0, 50) + '...' : field.value;
    lines.push(`  ✓ ${field.label || field.selector}: ${value}`);
  }
  lines.push('');
  
  // Skipped fields
  if (report.skippedFields.length > 0) {
    lines.push('───────────────────────────────────────────────────────────');
    lines.push(`  SKIPPED FIELDS (${report.skippedFields.length})`);
    lines.push('───────────────────────────────────────────────────────────');
    for (const field of report.skippedFields) {
      lines.push(`  ○ ${field.label || field.selector}: ${field.reason}`);
    }
    lines.push('');
  }
  
  // Fields requiring confirmation
  if (report.confirmRequired.length > 0) {
    lines.push('───────────────────────────────────────────────────────────');
    lines.push(`  ⚠️  REQUIRES CONFIRMATION (${report.confirmRequired.length})`);
    lines.push('───────────────────────────────────────────────────────────');
    for (const field of report.confirmRequired) {
      lines.push(`  ⚠ ${field.field}: ${field.reason}`);
      lines.push(`    Current value: ${JSON.stringify(field.current_value)}`);
    }
    lines.push('');
  }
  
  // Errors
  if (report.errors.length > 0) {
    lines.push('───────────────────────────────────────────────────────────');
    lines.push(`  ✗ ERRORS (${report.errors.length})`);
    lines.push('───────────────────────────────────────────────────────────');
    for (const error of report.errors) {
      lines.push(`  ✗ ${error.type}: ${error.message}`);
    }
    lines.push('');
  }
  
  // Screenshots
  if (report.screenshots.length > 0) {
    lines.push('───────────────────────────────────────────────────────────');
    lines.push('  SCREENSHOTS');
    lines.push('───────────────────────────────────────────────────────────');
    for (const screenshot of report.screenshots) {
      lines.push(`  📸 ${screenshot.stage}: ${screenshot.path}`);
    }
    lines.push('');
  }
  
  lines.push('═══════════════════════════════════════════════════════════');
  
  return lines.join('\n');
}

/**
 * Save report to file
 */
async function saveReport(report, applicationId) {
  const reportsDir = path.join(__dirname, '..', '..', 'reports');
  if (!fs.existsSync(reportsDir)) {
    fs.mkdirSync(reportsDir, { recursive: true });
  }
  
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `autofill_${applicationId}_${timestamp}`;
  
  // Save JSON report
  const jsonPath = path.join(reportsDir, `${filename}.json`);
  fs.writeFileSync(jsonPath, JSON.stringify(report, null, 2));
  
  // Save human-readable report
  const textPath = path.join(reportsDir, `${filename}.txt`);
  fs.writeFileSync(textPath, generateReport(report));
  
  return jsonPath;
}

/**
 * Log filled field
 */
function logFilledField(fieldName, value, selector) {
  return {
    field: fieldName,
    selector,
    value: String(value).substring(0, 100),
    timestamp: new Date().toISOString(),
  };
}

/**
 * Log skipped field
 */
function logSkippedField(fieldName, reason, selector) {
  return {
    field: fieldName,
    selector,
    reason,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Log error
 */
function logError(type, message, selector = null) {
  return {
    type,
    message,
    selector,
    timestamp: new Date().toISOString(),
  };
}

module.exports = {
  generateReport,
  saveReport,
  logFilledField,
  logSkippedField,
  logError,
};
