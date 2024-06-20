import { logError } from './helpers';

const encoder = new TextEncoder();
const decoder = new TextDecoder();

/**
 * These array buffer conversion functions are from Crypto API official documentation examples
 * https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/importKey
 * https://developers.google.com/web/updates/2012/06/How-to-convert-ArrayBuffer-to-and-from-String
 */
const str2ab = (str: string): ArrayBuffer => {
  const buf = new ArrayBuffer(str.length);
  const bufView = new Uint8Array(buf);
  for (let i = 0, strLen = str.length; i < strLen; i += 1) {
    bufView[i] = str.charCodeAt(i);
  }
  return buf;
};

const ab2str = (buffer: ArrayBuffer): string =>
  String.fromCharCode.apply(null, Array.from(new Uint8Array(buffer)));

function base64ToUint8Array(base64: string): Uint8Array {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i += 1) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}

/**
 * Generate AES key used to encrypt the secret value
 */
export const getAESKey = async (key?: Uint8Array | undefined): Promise<CryptoKey> => {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const algo = { name: 'AES-GCM', iv };

  let useKey: Uint8Array;
  if (!key) {
    // Use the encryption key (which must've been provided by the backend) if a key is not available.
    const keyBas64 = window.ENCRYPTION_KEY;
    if (!keyBas64) {
      throw new Error(
        'Unable to encrypt because ENCRYPTION_KEY is not available and was not passed as a parameter.',
      );
    }
    useKey = base64ToUint8Array(keyBas64);
  } else {
    useKey = key;
  }

  return crypto.subtle.importKey('raw', useKey, algo, false, ['encrypt', 'decrypt']);
};

interface EncryptedValue {
  value: string;
  iv: string;
  AESkey: CryptoKey;
  authTag: string;
}

/**
 * Generates AES key and encrypts the secret value with it
 */
export const encrypt = async (
  data: string | undefined,
  AESkey?: CryptoKey | undefined,
): Promise<EncryptedValue> => {
  let useKey: CryptoKey;
  if (!AESkey) {
    useKey = await getAESKey();
  } else {
    useKey = AESkey;
  }
  const generatedIv: Uint8Array = crypto.getRandomValues(new Uint8Array(16));
  const encodedValue: Uint8Array = encoder.encode(data);
  const encryptedValueBuf = await crypto.subtle.encrypt(
    {
      name: 'AES-GCM',
      iv: generatedIv,
      tagLength: 128,
    },
    useKey,
    encodedValue,
  );

  // WEB Crypto API attaches the auth tag at the end of the encrypted value but does not offer a function to export the GCM auth tag
  // We need to get the 128 bit tag from the end by slicing 16 bytes from the end of the encrypted value
  const authTagBuf = encryptedValueBuf.slice(encryptedValueBuf.byteLength - 16);

  // We will also trim the encrytped value to not contain the auth tag as backend does not support it
  const trimmedEncryptedValueBuf = encryptedValueBuf.slice(0, encryptedValueBuf.byteLength - 16);

  // Encode the string to base64
  const value = btoa(ab2str(trimmedEncryptedValueBuf));
  const iv = btoa(ab2str(generatedIv.buffer));
  const authTag = btoa(ab2str(authTagBuf));

  return {
    value,
    iv,
    AESkey: useKey,
    authTag,
  };
};

/**
 * Uses the AES key to decrypt the secret value
 */
export const decrypt = async (
  encryptedSecret: EncryptedValue,
  AESKey?: CryptoKey | undefined,
): Promise<string> => {
  let useKey: CryptoKey;
  if (!AESKey) {
    useKey = await getAESKey();
  } else {
    useKey = AESKey;
  }
  const authTagString = atob(encryptedSecret.authTag);
  const encryptedValueString = atob(encryptedSecret.value);

  // Backend Node crypto API has encryption value and auth tag separately.
  // However WEB Crypto API needs them together so we need to concat the auth tag at the end
  const cipherText = encryptedValueString + authTagString;
  const encryptedValueBuffer: ArrayBuffer = str2ab(cipherText);
  const encodedValue: Uint8Array = new Uint8Array(encryptedValueBuffer);

  try {
    const valueBuffer: ArrayBuffer = await crypto.subtle.decrypt(
      {
        name: 'AES-GCM',
        iv: str2ab(atob(encryptedSecret.iv)),
      },
      useKey,
      encodedValue,
    );
    const value = decoder.decode(valueBuffer);
    return value;
  } catch (error) {
    logError(error);
    throw error;
  }
};
