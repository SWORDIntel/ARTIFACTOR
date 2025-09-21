import api from './api';
import { User } from '../types';

export const login = async (credentials: { email: string; password: string }) => {
  return api.post('/auth/login', credentials);
};

export const register = async (userData: { name: string; email: string; password: string }) => {
  return api.post('/auth/register', userData);
};

export const logout = async () => {
  return api.post('/auth/logout');
};

export const getCurrentUser = async () => {
  return api.get('/auth/me');
};

export const updateProfile = async (userData: Partial<User>) => {
  return api.put('/auth/profile', userData);
};

export const refreshToken = async () => {
  return api.post('/auth/refresh');
};