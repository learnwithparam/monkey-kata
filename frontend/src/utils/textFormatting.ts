/**
 * Text formatting utilities for fixing common streaming issues
 * and normalizing spacing in AI-generated content.
 */

/**
 * Normalizes spacing in text to fix common streaming issues:
 * - Letter followed by number: "a30" -> "a 30"
 * - Punctuation followed by letter: "meals:with" -> "meals: with"
 * - Comma/punctuation spacing: "evening,5-year-old" -> "evening, 5-year-old"
 * 
 * @param text - The text to normalize
 * @returns The normalized text with proper spacing
 */
export function normalizeSpacing(text: string): string {
  if (!text) return text;
  
  // Fix: letter followed by number (e.g., "a30" -> "a 30")
  // This handles cases like "a30 day workout" -> "a 30 day workout"
  // But avoid if it's part of a URL or already has proper spacing
  let normalized = text.replace(/([a-zA-Z])(\d)/g, (match, letter, digit, offset, string) => {
    // Check if this is part of a URL pattern (http, https, etc.)
    const before = string.substring(Math.max(0, offset - 10), offset);
    if (before.match(/https?:\/\/|www\./i)) {
      return match; // Don't modify URLs
    }
    return `${letter} ${digit}`;
  });
  
  // Fix: punctuation (colon, semicolon) followed by letter (e.g., "meals:with" -> "meals: with")
  // Note: This won't match URLs like "http://" because slash is not a letter
  normalized = normalized.replace(/([:;])([a-zA-Z])/g, '$1 $2');
  
  // Fix: punctuation (comma, exclamation, question) followed by letter without space
  // Note: We avoid period to preserve decimals like "3.14" and abbreviations like "Dr."
  normalized = normalized.replace(/([,!?])([a-zA-Z])/g, '$1 $2');
  
  return normalized;
}

