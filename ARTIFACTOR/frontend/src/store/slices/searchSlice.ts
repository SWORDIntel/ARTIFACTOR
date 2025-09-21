import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { SearchQuery, SearchResult } from '../../types';
import * as searchService from '../../services/searchService';

interface SearchState {
  query: string;
  results: SearchResult | null;
  recentSearches: string[];
  isLoading: boolean;
  error: string | null;
}

const initialState: SearchState = {
  query: '',
  results: null,
  recentSearches: JSON.parse(localStorage.getItem('artifactor_recent_searches') || '[]'),
  isLoading: false,
  error: null,
};

export const performSearch = createAsyncThunk(
  'search/performSearch',
  async (searchQuery: SearchQuery, { rejectWithValue }) => {
    try {
      const response = await searchService.search(searchQuery);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Search failed');
    }
  }
);

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    setQuery: (state, action: PayloadAction<string>) => {
      state.query = action.payload;
    },
    addRecentSearch: (state, action: PayloadAction<string>) => {
      const query = action.payload.trim();
      if (query && !state.recentSearches.includes(query)) {
        state.recentSearches.unshift(query);
        state.recentSearches = state.recentSearches.slice(0, 10); // Keep only 10 recent searches
        localStorage.setItem('artifactor_recent_searches', JSON.stringify(state.recentSearches));
      }
    },
    clearRecentSearches: (state) => {
      state.recentSearches = [];
      localStorage.removeItem('artifactor_recent_searches');
    },
    clearResults: (state) => {
      state.results = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(performSearch.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(performSearch.fulfilled, (state, action) => {
        state.isLoading = false;
        state.results = action.payload;
      })
      .addCase(performSearch.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { setQuery, addRecentSearch, clearRecentSearches, clearResults } = searchSlice.actions;
export default searchSlice.reducer;