import { useState, useEffect, useCallback } from 'react';

interface OfflineAction {
  id: string;
  type: 'upload' | 'update' | 'delete' | 'collaboration';
  data: any;
  timestamp: number;
  retryCount: number;
}

interface SyncStatus {
  isOnline: boolean;
  isSyncing: boolean;
  pendingActions: number;
  lastSyncTime: Date | null;
  syncErrors: string[];
}

export const useOfflineSync = () => {
  const [syncStatus, setSyncStatus] = useState<SyncStatus>({
    isOnline: navigator.onLine,
    isSyncing: false,
    pendingActions: 0,
    lastSyncTime: null,
    syncErrors: [],
  });

  // IndexedDB operations
  const openDB = useCallback((): Promise<IDBDatabase> => {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('artifactor-offline', 1);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        if (!db.objectStoreNames.contains('actions')) {
          const actionsStore = db.createObjectStore('actions', { keyPath: 'id' });
          actionsStore.createIndex('timestamp', 'timestamp');
          actionsStore.createIndex('type', 'type');
        }

        if (!db.objectStoreNames.contains('artifacts')) {
          const artifactsStore = db.createObjectStore('artifacts', { keyPath: 'id' });
          artifactsStore.createIndex('lastModified', 'lastModified');
        }
      };
    });
  }, []);

  // Store offline action
  const storeOfflineAction = useCallback(async (action: Omit<OfflineAction, 'id' | 'timestamp' | 'retryCount'>) => {
    try {
      const db = await openDB();
      const transaction = db.transaction(['actions'], 'readwrite');
      const store = transaction.objectStore('actions');

      const offlineAction: OfflineAction = {
        ...action,
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: Date.now(),
        retryCount: 0,
      };

      await new Promise<void>((resolve, reject) => {
        const request = store.add(offlineAction);
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
      });

      // Update pending actions count
      const pendingActions = await getPendingActionsCount();
      setSyncStatus(prev => ({ ...prev, pendingActions }));

      // Register background sync if service worker is available
      if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register(`sync-${action.type}`);
      }

      return offlineAction.id;
    } catch (error) {
      console.error('Failed to store offline action:', error);
      throw error;
    }
  }, [openDB]);

  // Get pending actions count
  const getPendingActionsCount = useCallback(async (): Promise<number> => {
    try {
      const db = await openDB();
      const transaction = db.transaction(['actions'], 'readonly');
      const store = transaction.objectStore('actions');

      return new Promise<number>((resolve, reject) => {
        const request = store.count();
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('Failed to get pending actions count:', error);
      return 0;
    }
  }, [openDB]);

  // Get all pending actions
  const getPendingActions = useCallback(async (): Promise<OfflineAction[]> => {
    try {
      const db = await openDB();
      const transaction = db.transaction(['actions'], 'readonly');
      const store = transaction.objectStore('actions');

      return new Promise<OfflineAction[]>((resolve, reject) => {
        const request = store.getAll();
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('Failed to get pending actions:', error);
      return [];
    }
  }, [openDB]);

  // Remove completed action
  const removeAction = useCallback(async (actionId: string) => {
    try {
      const db = await openDB();
      const transaction = db.transaction(['actions'], 'readwrite');
      const store = transaction.objectStore('actions');

      await new Promise<void>((resolve, reject) => {
        const request = store.delete(actionId);
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
      });

      // Update pending actions count
      const pendingActions = await getPendingActionsCount();
      setSyncStatus(prev => ({ ...prev, pendingActions }));
    } catch (error) {
      console.error('Failed to remove action:', error);
    }
  }, [openDB, getPendingActionsCount]);

  // Sync pending actions
  const syncPendingActions = useCallback(async () => {
    if (!navigator.onLine) {
      console.log('Cannot sync: offline');
      return;
    }

    setSyncStatus(prev => ({ ...prev, isSyncing: true, syncErrors: [] }));

    try {
      const pendingActions = await getPendingActions();
      const errors: string[] = [];

      for (const action of pendingActions) {
        try {
          // Attempt to sync the action
          await syncAction(action);
          await removeAction(action.id);
        } catch (error) {
          console.error(`Failed to sync action ${action.id}:`, error);
          errors.push(`Failed to sync ${action.type}: ${error.message}`);

          // Implement retry logic
          if (action.retryCount < 3) {
            // Update retry count
            const db = await openDB();
            const transaction = db.transaction(['actions'], 'readwrite');
            const store = transaction.objectStore('actions');

            const updatedAction = { ...action, retryCount: action.retryCount + 1 };
            store.put(updatedAction);
          } else {
            // Max retries reached, remove action
            await removeAction(action.id);
            errors.push(`Max retries reached for ${action.type}, action discarded`);
          }
        }
      }

      setSyncStatus(prev => ({
        ...prev,
        isSyncing: false,
        lastSyncTime: new Date(),
        syncErrors: errors,
      }));
    } catch (error) {
      console.error('Sync failed:', error);
      setSyncStatus(prev => ({
        ...prev,
        isSyncing: false,
        syncErrors: [`Sync failed: ${error.message}`],
      }));
    }
  }, [getPendingActions, removeAction, openDB]);

  // Sync individual action based on type
  const syncAction = async (action: OfflineAction): Promise<void> => {
    const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';

    switch (action.type) {
      case 'upload':
        const uploadResponse = await fetch(`${baseUrl}/api/artifacts/upload`, {
          method: 'POST',
          body: action.data,
        });
        if (!uploadResponse.ok) {
          throw new Error(`Upload failed: ${uploadResponse.statusText}`);
        }
        break;

      case 'update':
        const updateResponse = await fetch(`${baseUrl}/api/artifacts/${action.data.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(action.data),
        });
        if (!updateResponse.ok) {
          throw new Error(`Update failed: ${updateResponse.statusText}`);
        }
        break;

      case 'delete':
        const deleteResponse = await fetch(`${baseUrl}/api/artifacts/${action.data.id}`, {
          method: 'DELETE',
        });
        if (!deleteResponse.ok) {
          throw new Error(`Delete failed: ${deleteResponse.statusText}`);
        }
        break;

      case 'collaboration':
        const collabResponse = await fetch(`${baseUrl}/api/collaboration/sync`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(action.data),
        });
        if (!collabResponse.ok) {
          throw new Error(`Collaboration sync failed: ${collabResponse.statusText}`);
        }
        break;

      default:
        throw new Error(`Unknown action type: ${action.type}`);
    }
  };

  // Handle online/offline events
  useEffect(() => {
    const handleOnline = () => {
      setSyncStatus(prev => ({ ...prev, isOnline: true }));
      // Automatically sync when coming back online
      setTimeout(syncPendingActions, 1000);
    };

    const handleOffline = () => {
      setSyncStatus(prev => ({ ...prev, isOnline: false }));
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [syncPendingActions]);

  // Listen for sync events from service worker
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data.type === 'UPLOAD_SYNCED') {
          // Handle successful sync notification
          syncPendingActions();
        }
      });
    }
  }, [syncPendingActions]);

  // Initialize pending actions count
  useEffect(() => {
    const loadPendingCount = async () => {
      const count = await getPendingActionsCount();
      setSyncStatus(prev => ({ ...prev, pendingActions: count }));
    };

    loadPendingCount();
  }, [getPendingActionsCount]);

  return {
    syncStatus,
    storeOfflineAction,
    syncPendingActions,
    getPendingActions,
  };
};