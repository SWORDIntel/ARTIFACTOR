import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  LinearProgress,
  Chip,
  alpha,
  useTheme,
} from '@mui/material';
import {
  Psychology as PsychologyIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';

const MLClassification: React.FC = () => {
  const theme = useTheme();

  const mockMetrics = {
    accuracy: 87.3,
    precision: 91.2,
    recall: 84.7,
    f1Score: 87.8,
  };

  const mockCategories = [
    { name: 'Frontend Development', confidence: 94.2, color: theme.palette.primary.main },
    { name: 'Backend API', confidence: 88.7, color: theme.palette.secondary.main },
    { name: 'Machine Learning', confidence: 91.5, color: theme.palette.success.main },
    { name: 'Data Processing', confidence: 76.3, color: theme.palette.warning.main },
    { name: 'DevOps', confidence: 82.1, color: theme.palette.info.main },
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
        ML Classification
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Automatic artifact categorization with 87.3% accuracy using machine learning
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card
            sx={{
              background: alpha(theme.palette.background.paper, 0.8),
              backdropFilter: 'blur(20px)',
              border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
              borderRadius: '16px',
              mb: 3,
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Classification Results
              </Typography>
              
              {mockCategories.map((category, index) => (
                <Box key={category.name} sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body1" sx={{ fontWeight: 500 }}>
                      {category.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {category.confidence}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={category.confidence}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: alpha(category.color, 0.2),
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: category.color,
                        borderRadius: 4,
                      },
                    }}
                  />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card
            sx={{
              background: alpha(theme.palette.background.paper, 0.8),
              backdropFilter: 'blur(20px)',
              border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
              borderRadius: '16px',
              mb: 3,
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Model Performance
              </Typography>
              
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <PsychologyIcon sx={{ color: theme.palette.primary.main }} />
                  <Box>
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>
                      {mockMetrics.accuracy}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Overall Accuracy
                    </Typography>
                  </Box>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <TrendingUpIcon sx={{ color: theme.palette.success.main }} />
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {mockMetrics.precision}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Precision
                    </Typography>
                  </Box>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <AssessmentIcon sx={{ color: theme.palette.info.main }} />
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {mockMetrics.recall}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Recall
                    </Typography>
                  </Box>
                </Box>
                
                <Chip
                  label={`F1-Score: ${mockMetrics.f1Score}%`}
                  sx={{
                    background: alpha(theme.palette.secondary.main, 0.1),
                    color: theme.palette.secondary.main,
                    fontWeight: 600,
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MLClassification;