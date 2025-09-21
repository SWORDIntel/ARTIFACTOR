import api from './api';
import { SearchQuery } from '../types';

export const search = async (query: SearchQuery) => {
  return api.post('/search', query);
};

export const getSearchSuggestions = async (query: string) => {
  return api.get('/search/suggestions', { params: { q: query } });
};

export const getPopularSearches = async () => {
  return api.get('/search/popular');
};