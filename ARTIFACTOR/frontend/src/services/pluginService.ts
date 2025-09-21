import api from './api';

export const getPlugins = async () => {
  return api.get('/plugins');
};

export const getPluginById = async (id: string) => {
  return api.get(`/plugins/${id}`);
};

export const installPlugin = async (id: string) => {
  return api.post(`/plugins/${id}/install`);
};

export const uninstallPlugin = async (id: string) => {
  return api.delete(`/plugins/${id}/install`);
};

export const enablePlugin = async (id: string) => {
  return api.put(`/plugins/${id}/enable`);
};

export const disablePlugin = async (id: string) => {
  return api.put(`/plugins/${id}/disable`);
};