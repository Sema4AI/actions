import { Dispatch, SetStateAction, useEffect, useState } from 'react';
import { decrypt, encrypt } from './encryption';

// This may be set by the server so that we can encrypt the data in the local storage.
declare global {
  interface Window {
    ENCRYPTION_KEY: string;
  }
}

if (!window.ENCRYPTION_KEY) {
  console.log(
    'Note: ENCRYPTION_KEY not available (data saved in localStorage will not be encrypted).',
  );
}

const getFromLocalStorage = async <T>(key: string, fallback: T, merge: boolean): Promise<T> => {
  const localValue = window?.localStorage.getItem(key);

  try {
    if (localValue) {
      const contents = JSON.parse(localValue);
      if (typeof contents === 'object') {
        const keys = Object.keys(contents);
        if (keys.length === 2 && keys.includes('__encrypted__') && keys.includes('encryptedData')) {
          // The data is encrypted, we need to decrypt it.
          const decrypted = await decrypt(contents.encryptedData);
          const parsed = JSON.parse(decrypted) as T;
          return merge ? { ...fallback, ...parsed } : parsed;
        }
      }

      // It's not encrypted: use as is.
      const parsed = contents as T;
      return merge ? { ...fallback, ...parsed } : parsed;
    }
  } catch (err) {
    return fallback;
  }

  return fallback;
};

const setToLocalStorage = async (key: string, payload: any): Promise<void> => {
  let data = JSON.stringify(payload);

  if (window.ENCRYPTION_KEY) {
    const encryptedData = await encrypt(data);
    data = JSON.stringify({ __encrypted__: 1, encryptedData: encryptedData });
  }

  console.log('set to local storage', key, data);
  window?.localStorage.setItem(key, data);
};

export const useLocalStorage = <T>(
  key: string,
  initialValue: T,
  merge = false,
): [T, Dispatch<SetStateAction<T>>] => {
  const [payload, setPayload] = useState<T>(initialValue);

  useEffect(() => {
    async function update() {
      const payload = await getFromLocalStorage(key, initialValue, merge);
      console.log('gotten from local storage', payload);
      setToLocalStorage(key, payload);
    }

    update();
  }, [payload]);

  return [payload, setPayload];
};
