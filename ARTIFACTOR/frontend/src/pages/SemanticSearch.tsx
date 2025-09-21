import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  InputAdornment,
  Grid,
  Chip,
  Avatar,
  IconButton,
  alpha,
  useTheme,
} from '@mui/material';
import {
  Search as SearchIcon,
  Star as StarIcon,
  Visibility as VisibilityIcon,
  Comment as CommentIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';

const SemanticSearch: React.FC = () => {
  const theme = useTheme();
  const [searchQuery, setSearchQuery] = useState('');

  const mockResults = [
    {
      id: '1',
      title: 'Advanced React Dashboard Components',
      description: 'Enterprise-grade dashboard with dark theme support',
      relevance: 95.8,
      tags: ['React', 'TypeScript', 'Dashboard'],
      views: 342,
      stars: 28,
    },
    {
      id: '2',
      title: 'ML Classification Pipeline',
      description: 'Complete machine learning pipeline for classification',
      relevance: 87.3,
      tags: ['Python', 'ML', 'Classification'],
      views: 156,
      stars: 15,
    },
  ];

  const mockSuggestions = [
    'React components',
    'Machine learning',
    'API integration',
    'Database queries',
    'Authentication',
  ];

  return (
    <Box>
      <Typography
        variant="h4"
        sx={{
          fontWeight: 700,
          mb: 1,
          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #c084fc 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}
      >
        Semantic Search
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Natural language search with vector similarity matching
      </Typography>

      {/* Search Interface */}
      <Card
        sx={{
          background: alpha(theme.palette.background.paper, 0.8),
          backdropFilter: 'blur(20px)',
          border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          borderRadius: '16px',
          mb: 4,
        }}
      >
        <CardContent sx={{ p: 4 }}>
          <TextField
            fullWidth
            placeholder="Search for artifacts using natural language..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ color: theme.palette.primary.main }} />
                </InputAdornment>
              ),
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: '16px',
                fontSize: '1.1rem',
                py: 1,
                background: alpha(theme.palette.background.default, 0.5),
              },
            }}
          />
          
          {/* Search Suggestions */}
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Popular searches:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {mockSuggestions.map((suggestion) => (
                <Chip
                  key={suggestion}
                  label={suggestion}
                  variant="outlined"
                  size="small"
                  clickable
                  onClick={() => setSearchQuery(suggestion)}
                  sx={{
                    borderColor: alpha(theme.palette.primary.main, 0.3),
                    color: theme.palette.primary.main,
                    '&:hover': {
                      backgroundColor: alpha(theme.palette.primary.main, 0.1),
                    },
                  }}
                />
              ))}
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Search Results */}
      <Grid container spacing={3}>
        {mockResults.map((result) => (
          <Grid item xs={12} key={result.id}>
            <Card
              sx={{
                background: alpha(theme.palette.background.paper, 0.8),
                backdropFilter: 'blur(20px)',
                border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
                borderRadius: '16px',
                transition: 'all 0.3s ease-in-out',
                cursor: 'pointer',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: '0 12px 40px rgba(99, 102, 241, 0.2)',
                  border: `1px solid ${alpha(theme.palette.primary.main, 0.3)}`,
                },
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 3 }}>
                  <Avatar
                    sx={{
                      background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                      width: 56,
                      height: 56,
                    }}
                  >
                    {result.title[0]}
                  </Avatar>
                  
                  <Box sx={{ flex: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {result.title}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <TrendingUpIcon sx={{ fontSize: 16, color: theme.palette.success.main }} />
                        <Typography variant="body2" color="success.main" sx={{ fontWeight: 600 }}>
                          {result.relevance}% match
                        </Typography>
                      </Box>
                    </Box>
                    
                    <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                      {result.description}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        {result.tags.map((tag) => (
                          <Chip
                            key={tag}
                            label={tag}
                            size="small"
                            sx={{
                              background: alpha(theme.palette.primary.main, 0.1),
                              color: theme.palette.primary.main,
                              border: `1px solid ${alpha(theme.palette.primary.main, 0.3)}`,
                            }}
                          />
                        ))}
                      </Box>
                      
                      <Box sx={{ display: 'flex', gap: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <VisibilityIcon fontSize="small" color="action" />
                          <Typography variant="caption">{result.views}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <StarIcon fontSize="small" color="action" />
                          <Typography variant="caption">{result.stars}</Typography>
                        </Box>
                      </Box>
                    </Box>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default SemanticSearch;