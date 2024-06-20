/* eslint-disable no-console */
/* eslint-disable @typescript-eslint/no-explicit-any */

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
    // Just ignore, a fallback will be returned
  }

  return fallback;
};

const setToLocalStorage = async (key: string, payload: any): Promise<void> => {
  let data = JSON.stringify(payload);

  if (window.ENCRYPTION_KEY) {
    const encryptedData = await encrypt(data);
    data = JSON.stringify({ __encrypted__: 1, encryptedData });
  }

  window?.localStorage.setItem(key, data);
};

/**
 * Saves/loads the values from the local storage based on the given key.
 *
 * Important: as values need to be saved in the local storage, they're converted
 * back and forth as json. As such, only objects convertable are supported
 * (i.e.: no Map, Set, etc. should be used).
 *
 * @param key The key to be used to save in the local storage
 * @param initialValue The initial value in case the value was never added to the local storage
 * @param merge A flag to identify whether the value in the local storage should be loaded with the initialValue
 */
export const useLocalStorage = <T>(
  key: string,
  initialValue: T,
  merge = false,
): [T, Dispatch<SetStateAction<T>>] => {
  const [payload, setPayload] = useState<T>(initialValue);
  const [loaded, setLoaded] = useState<boolean>(false);

  useEffect(() => {
    async function loadInitial() {
      const payloadInStorage = await getFromLocalStorage(key, initialValue, merge);
      setPayload(payloadInStorage);
      setLoaded(true);
    }
    loadInitial();
  }, []);

  useEffect(() => {
    if (loaded) {
      setToLocalStorage(key, payload);
    }
  }, [payload, loaded]);

  return [payload, setPayload];
};
