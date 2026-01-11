/**
 * Slugify utility functions for URL generation.
 *
 * These functions match the backend's URL slug transformation logic from:
 * sema4ai/action_server/_slugify.py and _api_action_routes.py
 *
 * The backend registers action routes with slugified names, so the frontend
 * must apply the same transformation when building API URLs.
 */

/**
 * Convert a string to a URL-safe slug.
 *
 * - Converts to lowercase
 * - Removes characters that aren't alphanumeric, whitespace, or hyphens
 * - Collapses multiple spaces/hyphens into single hyphens
 * - Strips leading/trailing hyphens and underscores
 */
export function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[-\s]+/g, '-')
    .replace(/^[-_]+|[-_]+$/g, '');
}

/**
 * Convert an action/package name to a URL path segment.
 *
 * This matches the backend's _name_to_url() function:
 * 1. Replace underscores with hyphens
 * 2. Apply slugify transformation
 *
 * Example: "get_wikipedia_article_summary" -> "get-wikipedia-article-summary"
 */
export function nameToUrl(name: string): string {
  return slugify(name.replace(/_/g, '-'));
}
