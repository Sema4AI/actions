/* eslint-disable @typescript-eslint/no-explicit-any */
import { expect, test } from 'vitest';
import { decrypt, encrypt, getAESKey } from '~/lib/encryption';

test('Encryption', async () => {
  const key = crypto.getRandomValues(new Uint8Array(32));
  const aesKey = await getAESKey(key);

  const encrypted = await encrypt('SOME DATA', aesKey);
  expect(encrypted.value).not.toBe('SOME DATA');

  const decrypted = await decrypt(encrypted, aesKey);
  expect(decrypted).toBe('SOME DATA');
});
