export function logError(err: unknown) {
  if (err instanceof Error) {
    const indent = '    ';
    if (err.message) {
      // eslint-disable-next-line no-console
      console.error(indent + err.message);
    }
    if (err.stack) {
      const stack = `${err.stack}`;
      // eslint-disable-next-line no-console
      console.error(stack.replace(/^/gm, indent));
    }
  }
}

export class Counter {
  private count: number;

  constructor(initial = 0) {
    this.count = initial;
  }

  public next(): number {
    this.count += 1;
    return this.count;
  }
}

export function copyArrayAndInsertElement<T>(array: T[], element: T, position: number): T[] {
  if (position < 0 || position > array.length) {
    throw new Error('Invalid position');
  }

  const newArray = array.slice(0, position); // creates copy

  // add new item in array copy
  newArray.push(element);

  // add remaining items to it
  for (let i = position; i < array.length; i += 1) {
    newArray.push(array[i]);
  }

  return newArray;
}

export const prettyPrint = (input: string) => {
  try {
    return JSON.stringify(JSON.parse(input), null, 4);
  } catch {
    return input;
  }
};

export const toKebabCase = (str: string): string => {
  return str.replace(/[\s_]+/g, '-').toLowerCase();
};

/**
 * Download data as a JSON file
 * @param data - The data to download (will be stringified if not already a string)
 * @param filename - The filename (without extension)
 */
export const downloadAsJson = (data: unknown, filename: string): void => {
  const jsonString = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
  const blob = new Blob([jsonString], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Copy text to clipboard
 * @param text - The text to copy
 * @returns Promise that resolves to true if copy succeeded, false otherwise
 */
export const copyToClipboard = async (text: string): Promise<boolean> => {
  // Try modern clipboard API first
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // Fall through to fallback
    }
  }
  
  // Fallback for older browsers or insecure contexts
  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.style.position = 'fixed';
  textArea.style.left = '-999999px';
  textArea.style.top = '-999999px';
  textArea.style.opacity = '0';
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  
  try {
    const success = document.execCommand('copy');
    return success;
  } catch {
    console.warn('Copy to clipboard failed');
    return false;
  } finally {
    document.body.removeChild(textArea);
  }
};
