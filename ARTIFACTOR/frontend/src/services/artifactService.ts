import api from './api';
import { Artifact, SearchQuery, PaginationParams } from '../types';

export const getArtifacts = async (params: PaginationParams) => {
  return api.get('/artifacts', { params });
};

export const getArtifactById = async (id: string) => {
  return api.get(`/artifacts/${id}`);
};

export const createArtifact = async (artifactData: Partial<Artifact>) => {
  return api.post('/artifacts', artifactData);
};

export const updateArtifact = async (id: string, data: Partial<Artifact>) => {
  return api.put(`/artifacts/${id}`, data);
};

export const deleteArtifact = async (id: string) => {
  return api.delete(`/artifacts/${id}`);
};

export const bulkDeleteArtifacts = async (ids: string[]) => {
  return api.delete('/artifacts/bulk', { data: { ids } });
};

export const searchArtifacts = async (query: SearchQuery) => {
  return api.post('/artifacts/search', query);
};

export const getArtifactVersions = async (id: string) => {
  return api.get(`/artifacts/${id}/versions`);
};

export const cloneArtifact = async (id: string) => {
  return api.post(`/artifacts/${id}/clone`);
};

export const shareArtifact = async (id: string, shareData: { users: string[]; permissions: string[] }) => {
  return api.post(`/artifacts/${id}/share`, shareData);
};