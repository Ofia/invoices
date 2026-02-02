import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { workspaces } from '../lib/api';
import type { Workspace } from '../lib/api/types';

interface WorkspaceContextType {
  currentWorkspace: Workspace | null;
  workspaceList: Workspace[];
  loading: boolean;
  setCurrentWorkspace: (workspace: Workspace) => void;
  refreshWorkspaces: () => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null);
  const [workspaceList, setWorkspaceList] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch workspaces on mount
  useEffect(() => {
    fetchWorkspaces();
  }, []);

  const fetchWorkspaces = async () => {
    try {
      setLoading(true);
      let list = await workspaces.list();

      // Auto-create default workspace if user has none
      if (list.length === 0) {
        const newWorkspace = await workspaces.create({ name: 'My Workspace' });
        list = [newWorkspace];
      }

      setWorkspaceList(list);

      // Restore from localStorage or select first
      const savedWorkspaceId = localStorage.getItem('current_workspace_id');
      if (savedWorkspaceId) {
        const saved = list.find((w) => w.id === parseInt(savedWorkspaceId));
        if (saved) {
          setCurrentWorkspace(saved);
          return;
        }
      }

      // Auto-select first workspace
      if (list.length > 0) {
        setCurrentWorkspace(list[0]);
        localStorage.setItem('current_workspace_id', list[0].id.toString());
      }
    } catch (error) {
      console.error('Failed to fetch workspaces:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSetCurrentWorkspace = (workspace: Workspace) => {
    setCurrentWorkspace(workspace);
    localStorage.setItem('current_workspace_id', workspace.id.toString());
  };

  const refreshWorkspaces = async () => {
    await fetchWorkspaces();
  };

  return (
    <WorkspaceContext.Provider
      value={{
        currentWorkspace,
        workspaceList,
        loading,
        setCurrentWorkspace: handleSetCurrentWorkspace,
        refreshWorkspaces,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used inside WorkspaceProvider');
  }
  return context;
}
